#ifndef SUZY_NATIVE_LOOP_H
#define SUZY_NATIVE_LOOP_H
#include <stdint.h>
typedef struct NL NL;
enum { NL_EMPTY, NL_ARMED, NL_RECORDING, NL_PLAYING, NL_DUB_QUEUED, NL_DUBBING, NL_STOPPED };
enum { NL_RECORD=1, NL_FINISH, NL_OVERDUB, NL_UNDO, NL_PLAY, NL_CLEAR };
typedef struct { uint32_t state, frames, position, revision, undo, rate, latency; double boundary; } NLStatus;
NL *nl_create(uint32_t rate);
void nl_destroy(NL *);
/* Single control producer. False means mailbox busy; caller must not pretend success. */
int nl_command(NL *, uint32_t command, uint32_t frames, uint32_t channel, double start);
void nl_stop(NL *);
void nl_gain(NL *, float gain);
NLStatus nl_status(NL *);
/* Audio-thread only: interleaved stereo, bounded block, time = first output frame. */
void nl_render(NL *, const float *input, float *output, uint32_t frames, double time, uint32_t latency);
/* Control thread acquires immutable snapshot; release before next acquire. */
const float *nl_snapshot(NL *, uint32_t *frames, uint32_t *revision);
void nl_release_snapshot(NL *);
/* macOS default input/output must be the same full-duplex device. Never reconfigures it. */
NL *nl_open(char *error, uint32_t capacity);
void nl_close(NL *);
int nl_fault(NL *);
#endif

#include "NativeLoop.h"
#include <stdlib.h>
#include <stdatomic.h>
#include <math.h>
#include <string.h>
#ifdef __APPLE__
#include <CoreAudio/CoreAudio.h>
#include <mach/mach_time.h>
#endif
struct NL {
    uint32_t rate, capacity, state, length, pos, count, target, channel, dubLatency, revision, undo, undoQueued;
    double start;
    float *base, *spare, *previous, *snapshot;
    uint32_t snapOffset, snapRevision, snapFrames;
    _Atomic unsigned mailbox, halt, gain, snapshotState, fault;
    uint32_t command, commandFrames, commandChannel; double commandStart;
    _Atomic unsigned pubState, pubLength, pubPos, pubRevision, pubUndo, pubLatency;
    /* Boundary uses lock-free 64-bit integer on supported Apple Silicon/x86_64. */
    _Atomic uint64_t boundaryNS;
#ifdef __APPLE__
    AudioDeviceID device; AudioDeviceIOProcID proc;
    double hostScale; float input[8192], output[8192];
#endif
};
NL *nl_create(uint32_t rate) {
    if (rate != 44100 && rate != 48000) return NULL;
    NL *e=calloc(1,sizeof(*e)); if (!e) return NULL;
    e->rate=rate; e->capacity=rate*8;
    e->base=calloc(e->capacity*2,sizeof(float)); e->spare=calloc(e->capacity*2,sizeof(float));
    e->previous=calloc(e->capacity*2,sizeof(float)); e->snapshot=calloc(e->capacity*2,sizeof(float));
    if (!e->base || !e->spare || !e->previous || !e->snapshot) { nl_destroy(e); return NULL; }
    atomic_init(&e->gain,60000); return e;
}
void nl_destroy(NL *e) { if(e) { free(e->base);free(e->spare);free(e->previous);free(e->snapshot);free(e); } }
int nl_command(NL *e,uint32_t c,uint32_t f,uint32_t ch,double t) {
    if (!e || atomic_load(&e->mailbox) || atomic_load(&e->halt) || c<NL_RECORD || c>NL_CLEAR || ch>2 || !isfinite(t)) return 0;
    if(c==NL_RECORD && (f<e->rate/4 || f>e->capacity)) return 0;
    e->command=c;e->commandFrames=f;e->commandChannel=ch;e->commandStart=t;
    atomic_store_explicit(&e->mailbox,1,memory_order_release);return 1;
}
void nl_stop(NL *e) { if(e) atomic_store(&e->halt,1); }
void nl_gain(NL *e,float g) { if(e) atomic_store(&e->gain,isfinite(g)?(unsigned)(fmaxf(0,fminf(1,g))*100000):0); }
NLStatus nl_status(NL *e) {
    NLStatus s={0}; if(!e)return s;
    s.state=atomic_load(&e->pubState);s.frames=atomic_load(&e->pubLength);s.position=atomic_load(&e->pubPos);
    s.revision=atomic_load(&e->pubRevision);s.undo=atomic_load(&e->pubUndo);s.rate=e->rate;
    s.latency=atomic_load(&e->pubLatency);s.boundary=(double)atomic_load(&e->boundaryNS)/1e9;return s;
}
const float *nl_snapshot(NL *e,uint32_t *f,uint32_t *r) {
    unsigned ready=2;
    if(!atomic_compare_exchange_strong(&e->snapshotState,&ready,3)) return NULL;
    *f=e->snapFrames;*r=e->snapRevision;return e->snapshot;
}
void nl_release_snapshot(NL *e) { atomic_store_explicit(&e->snapshotState,0,memory_order_release); }
static float safe(float x) { return isfinite(x)?fmaxf(-1,fminf(1,x)):0; }
static int active(NL *e) { return e->state==NL_PLAYING || e->state==NL_DUB_QUEUED || e->state==NL_DUBBING; }
static void finish(NL *e) { e->length=e->count;e->pos=0;e->state=NL_PLAYING;e->revision++; }
void nl_render(NL *e,const float *in,float *out,uint32_t n,double time,uint32_t latency) {
    if(!e || !out || n>4096) return;
    memset(out,0,n*2*sizeof(float));
    if(atomic_load_explicit(&e->halt,memory_order_acquire)) {
        atomic_store(&e->mailbox,0);e->state=e->length?NL_STOPPED:NL_EMPTY;e->count=0;e->undoQueued=0;
        atomic_store_explicit(&e->halt,0,memory_order_release);
    }
    if(atomic_load_explicit(&e->mailbox,memory_order_acquire)==1) {
        uint32_t c=e->command,f=e->commandFrames,ch=e->commandChannel;double start=e->commandStart;
        atomic_store_explicit(&e->mailbox,0,memory_order_release);
        if(c==NL_CLEAR) {e->length=0;e->pos=0;e->state=NL_EMPTY;e->undo=0;e->undoQueued=0;e->revision++;}
        if(c==NL_RECORD && !e->length) { e->target=f;e->channel=ch;e->start=start;e->count=0;e->state=NL_ARMED; }
        if(c==NL_FINISH && e->state==NL_RECORDING && e->count>=e->rate/4) finish(e);
        if(c==NL_OVERDUB && e->state==NL_PLAYING) e->state=NL_DUB_QUEUED;
        if(c==NL_PLAY && e->state==NL_STOPPED && e->length) {e->pos=0;e->state=NL_PLAYING;}
        if(c==NL_UNDO && e->undo && (e->state==NL_PLAYING || e->state==NL_STOPPED)) e->undoQueued=1;
    }
    if(e->undoQueued && e->state==NL_STOPPED) {
        float *p=e->base;e->base=e->previous;e->previous=p;e->undo=0;e->undoQueued=0;e->revision++;
    }
    float gain=(float)atomic_load(&e->gain)/100000;
    for(uint32_t i=0;i<n;i++) {
        double t=time+(double)i/e->rate;
        if(e->state==NL_ARMED && t>=e->start) e->state=NL_RECORDING;
        float l=in?safe(in[i*2]):0,r=in?safe(in[i*2+1]):0;
        if(e->channel<2) {l=e->channel==0?l:r;r=l;}
        if(e->state==NL_RECORDING) {
            e->base[e->count*2]=l;e->base[e->count*2+1]=r;
            if(++e->count==e->target) finish(e);
            continue; /* next frame is the first repeated sample, even inside this block */
        }
        if(!active(e)) continue;
        if(e->pos==0 && e->undoQueued) {
            float *p=e->base;e->base=e->previous;e->previous=p;e->undo=0;e->undoQueued=0;e->revision++;
        }
        if(e->pos==0 && e->state==NL_DUB_QUEUED) {e->state=NL_DUBBING;e->count=0;e->dubLatency=latency;}
        out[i*2]=e->base[e->pos*2]*gain;out[i*2+1]=e->base[e->pos*2+1]*gain;
        if(e->state==NL_DUBBING) {
            /* Input timestamp precedes output; place captured sound at its audible loop phase. */
            uint32_t p=(e->pos+e->length-e->dubLatency%e->length)%e->length;
            e->spare[p*2]=safe(e->base[p*2]+l);e->spare[p*2+1]=safe(e->base[p*2+1]+r);
            if(++e->count==e->length) {
                float *old=e->previous;e->previous=e->base;e->base=e->spare;e->spare=old;
                e->undo=1;e->revision++;e->state=NL_PLAYING;
            }
        }
        e->pos=(e->pos+1)%e->length;
    }
    /* Incremental immutable export: <=4096 frames copied per callback, never a whole-loop allocation. */
    unsigned ss=atomic_load_explicit(&e->snapshotState,memory_order_acquire);
    if(ss==0 && e->length && e->snapRevision!=e->revision) {e->snapOffset=0;e->snapFrames=e->length;e->snapRevision=e->revision;atomic_store(&e->snapshotState,1);ss=1;}
    if(ss==1) {
        if(!e->length || e->snapRevision!=e->revision) {e->snapRevision=0;atomic_store(&e->snapshotState,0);}
        else {uint32_t k=e->length-e->snapOffset;if(k>4096)k=4096;
            memcpy(e->snapshot+e->snapOffset*2,e->base+e->snapOffset*2,k*2*sizeof(float));e->snapOffset+=k;
            if(e->snapOffset==e->length)atomic_store_explicit(&e->snapshotState,2,memory_order_release);
        }
    }
    atomic_store(&e->pubState,e->state);atomic_store(&e->pubLength,e->length);atomic_store(&e->pubPos,e->pos);
    atomic_store(&e->pubRevision,e->revision);atomic_store(&e->pubUndo,e->undo);atomic_store(&e->pubLatency,latency);
    double boundary=active(e)?time+(double)(n+e->length-e->pos)/e->rate:0;
    atomic_store(&e->boundaryNS,(uint64_t)(fmax(0,boundary)*1e9));
}
int nl_fault(NL *e) {return e?atomic_load(&e->fault):0;}
#ifdef __APPLE__
#include <stdio.h>
static OSStatus property(AudioObjectID object,AudioObjectPropertySelector selector,AudioObjectPropertyScope scope,void *value,UInt32 size) {
    AudioObjectPropertyAddress a={selector,scope,kAudioObjectPropertyElementMain};
    return AudioObjectGetPropertyData(object,&a,0,NULL,&size,value);
}
static int validStreams(AudioDeviceID device,AudioObjectPropertyScope scope) {
    AudioObjectPropertyAddress a={kAudioDevicePropertyStreams,scope,kAudioObjectPropertyElementMain};UInt32 size=0;
    if(AudioObjectGetPropertyDataSize(device,&a,0,NULL,&size) || !size || size>64*sizeof(AudioStreamID))return 0;
    AudioStreamID streams[64]; if(AudioObjectGetPropertyData(device,&a,0,NULL,&size,streams))return 0;
    unsigned channels=0;
    for(unsigned i=0;i<size/sizeof(AudioStreamID);i++) {
        AudioStreamBasicDescription f={0};
        if(property(streams[i],kAudioStreamPropertyVirtualFormat,kAudioObjectPropertyScopeGlobal,&f,sizeof(f)) ||
            f.mFormatID!=kAudioFormatLinearPCM || !(f.mFormatFlags&kAudioFormatFlagIsFloat) ||
            (f.mFormatFlags&kAudioFormatFlagIsBigEndian) || f.mBitsPerChannel!=32 || f.mFramesPerPacket!=1) return 0;
        channels+=f.mChannelsPerFrame;
    }
    return channels>=2;
}
static OSStatus changed(AudioObjectID object,UInt32 count,const AudioObjectPropertyAddress addresses[],void *context) {
    (void)object;(void)count;(void)addresses;NL *e=context;atomic_store(&e->fault,1);return noErr;
}
static const AudioObjectPropertySelector watched[]={kAudioDevicePropertyNominalSampleRate,kAudioDevicePropertyDeviceIsAlive,kAudioDevicePropertyStreamConfiguration};
static float sample(const AudioBufferList *list,uint32_t frame,unsigned channel) {
    if(!list)return 0;
    for(UInt32 i=0;i<list->mNumberBuffers;i++) {
        const AudioBuffer *b=&list->mBuffers[i];
        if(channel<b->mNumberChannels) {
            uint64_t idx=(uint64_t)frame*b->mNumberChannels+channel;
            return b->mData && (idx+1)*sizeof(float)<=b->mDataByteSize?((float*)b->mData)[idx]:0;
        }
        channel-=b->mNumberChannels;
    }
    return 0;
}
static OSStatus process(AudioObjectID device,const AudioTimeStamp *now,const AudioBufferList *input,const AudioTimeStamp *inputTime,AudioBufferList *output,const AudioTimeStamp *outputTime,void *context) {
    (void)device;(void)now;NL *e=context;
    if(!output)return noErr;
    for(UInt32 j=0;j<output->mNumberBuffers;j++)if(output->mBuffers[j].mData)memset(output->mBuffers[j].mData,0,output->mBuffers[j].mDataByteSize);
    if(atomic_load(&e->fault))return noErr;
    uint32_t frames=0;
    for(UInt32 j=0;j<output->mNumberBuffers;j++) {
        AudioBuffer *b=&output->mBuffers[j];if(!b->mData || !b->mNumberChannels)continue;
        uint32_t f=b->mDataByteSize/(sizeof(float)*b->mNumberChannels);
        if(frames && frames!=f){atomic_store(&e->fault,1);return noErr;}frames=f;
    }
    if(!frames || frames>4096 || !(outputTime->mFlags&kAudioTimeStampHostTimeValid) || !(inputTime->mFlags&kAudioTimeStampHostTimeValid)) {atomic_store(&e->fault,1);return noErr;}
    double t=outputTime->mHostTime*e->hostScale;
    double latency=(t-inputTime->mHostTime*e->hostScale)*e->rate;
    if(latency<0 || latency>e->rate/2){atomic_store(&e->fault,1);return noErr;}
    for(uint32_t i=0;i<frames;i++){e->input[i*2]=sample(input,i,0);e->input[i*2+1]=sample(input,i,1);}
    nl_render(e,e->input,e->output,frames,t,(uint32_t)llround(latency));
    unsigned channel=0;
    for(UInt32 j=0;j<output->mNumberBuffers;j++) {
        AudioBuffer *b=&output->mBuffers[j];
        for(unsigned c=0;c<b->mNumberChannels;c++,channel++)if(channel<2 && b->mData)
            for(uint32_t i=0;i<frames;i++)((float*)b->mData)[i*b->mNumberChannels+c]=e->output[i*2+channel];
    }
    return noErr;
}
NL *nl_open(char *error,uint32_t cap) {
    AudioDeviceID input=0,output=0;Float64 rate=0;
    const char *reason="Select the same full-duplex interface (for example Focusrite) as macOS input and output.";
    if(property(kAudioObjectSystemObject,kAudioHardwarePropertyDefaultInputDevice,kAudioObjectPropertyScopeGlobal,&input,sizeof(input)) ||
       property(kAudioObjectSystemObject,kAudioHardwarePropertyDefaultOutputDevice,kAudioObjectPropertyScopeGlobal,&output,sizeof(output)) || !input || input!=output)goto fail;
    reason="Use a stereo 44.1 or 48 kHz interface with Float32 audio streams. Device settings were not changed.";
    if(property(input,kAudioDevicePropertyNominalSampleRate,kAudioObjectPropertyScopeGlobal,&rate,sizeof(rate)) ||
       (rate!=44100 && rate!=48000) || !validStreams(input,kAudioObjectPropertyScopeInput) || !validStreams(input,kAudioObjectPropertyScopeOutput))goto fail;
    NL *e=nl_create((uint32_t)rate);reason="Unable to allocate the bounded loop buffers.";if(!e)goto fail;
    e->device=input;mach_timebase_info_data_t info;mach_timebase_info(&info);e->hostScale=(double)info.numer/info.denom/1e9;
    reason="Unable to start interface audio. Check microphone permission and the interface connection.";
    if(AudioDeviceCreateIOProcID(input,process,e,&e->proc)){nl_destroy(e);goto fail;}
    for(unsigned i=0;i<3;i++) {
        AudioObjectPropertyAddress a={watched[i],kAudioObjectPropertyScopeGlobal,kAudioObjectPropertyElementMain};
        AudioObjectAddPropertyListener(input,&a,changed,e);
    }
    if(AudioDeviceStart(input,e->proc)){nl_close(e);goto fail;}return e;
fail:
    if(error && cap)snprintf(error,cap,"%s",reason);return NULL;
}
void nl_close(NL *e) {
    if(!e)return;
    if(e->proc)AudioDeviceStop(e->device,e->proc);
    for(unsigned i=0;i<3;i++) {
        AudioObjectPropertyAddress a={watched[i],kAudioObjectPropertyScopeGlobal,kAudioObjectPropertyElementMain};
        AudioObjectRemovePropertyListener(e->device,&a,changed,e);
    }
    if(e->proc)AudioDeviceDestroyIOProcID(e->device,e->proc);nl_destroy(e);
}
#else
NL *nl_open(char *error,uint32_t cap) {(void)error;(void)cap;return NULL;}
void nl_close(NL *e) {nl_destroy(e);}
#endif

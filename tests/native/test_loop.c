#include "NativeLoop.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#define RATE 48000
#define LENGTH 12000
static float input[8192],output[8192];
static uint64_t cursor;
static void render(NL *e,unsigned n,unsigned latency,float value) {
    for(unsigned i=0;i<n*2;i++)input[i]=value;
    nl_render(e,input,output,n,(double)cursor/RATE,latency);cursor+=n;
}
static void advance(NL *e,unsigned n,unsigned latency,float value) {
    while(n){unsigned k=n>317?317:n;render(e,k,latency,value);n-=k;}
}
static NL *record(float value) {
    NL *e=nl_create(RATE);assert(e);nl_gain(e,1);cursor=0;
    assert(nl_command(e,NL_RECORD,LENGTH,2,0));advance(e,LENGTH,0,value);
    assert(nl_status(e).state==NL_PLAYING);return e;
}
static void continuity(void) {
    NL *e=nl_create(RATE);nl_gain(e,1);cursor=0;
    assert(nl_command(e,NL_RECORD,LENGTH,0,0));advance(e,LENGTH-3,0,0.25f);
    render(e,9,0,0.25f);
    for(unsigned i=0;i<6;i++)assert(output[i]==0);
    for(unsigned i=6;i<18;i++)assert(output[i]==0.25f);
    advance(e,LENGTH*3+11,0,0);for(unsigned i=0;i<22;i++)assert(output[i]==0.25f);
    assert(nl_status(e).frames==LENGTH);nl_destroy(e);
}
static void overdubUndoAndCancel(void) {
    NL *e=record(0.125f);
    assert(nl_command(e,NL_OVERDUB,0,0,0));advance(e,LENGTH,0,0.25f);
    assert(nl_status(e).revision==2 && nl_status(e).undo);
    render(e,1,0,0);assert(output[0]==0.375f); /* no extra cycle */
    assert(nl_command(e,NL_UNDO,0,0,0));advance(e,LENGTH-1,0,0);
    render(e,1,0,0);assert(output[0]==0.125f);assert(!nl_status(e).undo);
    assert(nl_command(e,NL_OVERDUB,0,0,0));advance(e,LENGTH+100,0,0.5f);
    nl_stop(e);render(e,1,0,0);assert(output[0]==0 && nl_status(e).state==NL_STOPPED);
    assert(nl_command(e,NL_PLAY,0,0,0));render(e,1,0,0);assert(output[0]==0.125f);
    nl_destroy(e);
}
static void compensatedImpulse(void) {
    NL *e=record(0);assert(nl_command(e,NL_OVERDUB,0,0,0));
    /* Input arrives 20 samples behind output. Impulse captured at output frame 23 belongs at loop frame 3. */
    render(e,23,20,0);render(e,1,20,0.5f);advance(e,LENGTH-24,20,0);
    render(e,8,20,0);for(unsigned i=0;i<8;i++)assert(output[i*2]==(i==3?0.5f:0));nl_destroy(e);
}
static void snapshotAndPriority(void) {
    NL *e=record(0.25f);advance(e,1000,0,0);uint32_t f=0,r=0;
    const float *copy=nl_snapshot(e,&f,&r);assert(copy && f==LENGTH && r==1);
    assert(nl_command(e,NL_OVERDUB,0,0,0));advance(e,LENGTH*2,0,0.25f);
    for(unsigned i=0;i<LENGTH*2;i++)assert(copy[i]==0.25f);
    nl_release_snapshot(e);advance(e,1000,0,0);copy=nl_snapshot(e,&f,&r);assert(copy && r==2 && copy[0]==0.5f);nl_release_snapshot(e);
    assert(nl_command(e,NL_OVERDUB,0,0,0));assert(!nl_command(e,NL_CLEAR,0,0,0));
    nl_stop(e);render(e,1,0,0);assert(nl_status(e).state==NL_STOPPED);
    assert(nl_command(e,NL_CLEAR,0,0,0));render(e,1,0,0);assert(!nl_status(e).frames);nl_destroy(e);
}
static void boundariesAndValidation(void) {
    assert(!nl_create(96000));NL *e=nl_create(RATE);nl_gain(e,1);cursor=0;
    assert(!nl_command(e,NL_RECORD,1,0,0));assert(!nl_command(e,NL_RECORD,RATE*9,0,0));
    assert(nl_command(e,NL_RECORD,LENGTH,0,10.0/RATE));render(e,20,0,NAN);
    assert(nl_status(e).state==NL_RECORDING);advance(e,LENGTH-10,0,0.5f);
    assert(nl_status(e).state==NL_PLAYING);render(e,11,0,0);
    for(unsigned i=0;i<10;i++){assert(output[i*2]==0);}
    assert(output[20]==0.5f);
    assert(fabs(nl_status(e).boundary-(double)(10+LENGTH*2)/RATE)<1e-7);nl_destroy(e);
    e=record(0.125f);assert(nl_command(e,NL_RECORD,LENGTH,0,0));render(e,1,0,0);assert(output[0]==0.125f);nl_destroy(e);
}
int main(void) {continuity();overdubUndoAndCancel();compensatedImpulse();snapshotAndPriority();boundariesAndValidation();puts("Native loop: 5 timing/safety scenarios passed");}

# Teaching SUZY//AI what makes me laugh

**Build note · October 8, 2026**

SUZY//AI is now answering through a local model. The next experiment starts with
a question and a handful of music jokes.

## The thread

**What do you think about Mormon music?**

1. I'm partial to the The Joseph Smiths... The Mormonissey years, at least.
2. the (latter day) Saints
3. Detroit Salt City
4. Better Than Ezra...Just Ask Him
5. Mennonite At Work
6. Mission of Burma

These are the examples Suzy supplied and chose to share. Individual reply authors
are unspecified; this does not attribute every joke to Suzy or to the model.
Wording is preserved from the saved note, including the doubled “the”.

## What happened

Suzy saved the setup and all six replies together through the local memory API.
The API returned a successful saved-memory record. That establishes storage;
retrieval and the quality of new jokes are the next things to evaluate.

The current label is **humour / music / band-name wordplay**. It was assigned in
the assisted capture workflow, not automatically discovered by the local model.
The [JSON example](../../examples/threads/mormon-music.json) contains the same
approved input, without the private database ID or local machine details.

This is an early example of teaching through humour and musical taste: supply a
setup and the replies together, preserve their context, and see whether SUZY can
use them in a later conversation. There is no need to rate every reply or turn a
joke into a questionnaire before capturing it.

## What “learning” means here

Right now, this is persistent memory plus optional retrieval. Saving the thread
does not update model weights. `/memory on` lets subsequent chat requests retrieve
matching saved notes; ordinary chat and generated riffs are not automatically saved.

A first check is: “What were the replies in the Mormon music thread I saved?”
Then: “Using that thread as inspiration, write three new band-name jokes. Don't
explain the punchlines.” These are proposed checks, not reported model results.

The current store holds the whole exchange as one document. Automatic categorization
and individual reply relationships are future work.

## Building in public

This example was deliberately selected for publication by Suzy. It is a curated
public copy, not a sync of the private memory store. New build notes and examples
can be shared the same way when selected. Publishing this note does not enable
ongoing export of local conversations, memories, or model output.

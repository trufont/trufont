# What should an undo system be like for TruFont?

## Introduction to Undo Systems

An undo/redo stack is often implemented with as an “undo manager” class. In the case of an outline editor, a lot of data will simply be copied, as it’s not always possible to simply “perform the reverse operation”. Transformations are a good example of that. But also point behavior: when a handle is implicitly being moved because it has a “smooth” connection to another, the opposite movement may result in a different position of the “implied” movement due to rounding. So in general, we need to efficiently copy the complete previous state of an outline to be able to do undo reliably.

If diffing between versions can be done with text-representations of objects, the github.com/google/diff-match-patch library may be of interest; Python’s difflib is not really an option as it only does diffing, not patching.

Perhaps much of the code can be implemented as a separate library, for example called “tundo”.

## Considerations about resource usage

Should all undo data be kept in RAM (possibly limiting the number of undo levels to be kept) or should undo data be flushed to disk, to minimize RAM usage?

## Factoring

From the perspective of the UI and object code, the undo API should be simple. Objects may have to provide efficient way to serialize themselves (either as binary data or as text), but the undo manager will take care of storing data efficiently. The undo API will have no notion about how efficiently or inefficiently the undo data is stored. Whether data is stored in memory or on disk will be completely opaque to the undo client. This will allow us to build a working system first, and then measure and optimize for performance and resource usage.

## Undo vs Selection

Undo is not only about the model data, but also selection data: if you do a step back with undo, the user also expects the selection to be the same as before. This notion is important because it implies undo data is more than just serialization of glyph data.

Perhaps the tfont library should support a serialization format that is specialized for undo, in that it contains selection info. I need to figure out how this needs to be factored. Perhaps the “converter” concept can be used.

## Undo vs Redo

Each UndoManager should maintain an undo stack and a redo stack. When editing data, before the edit is applied, the current version of the data should be added to the undo stack. Performing undo is also an edit operation, but it’s special in that the current state of the data is now added to the redo stack. The design of the undo manager should make implementing this behavior easy.

## Undo vs Notifications

Depending on how notifications are done in TruFont, some leverage may be gained from pairing undo with the notification mechanism. A more general notification system may allow this more easily. (Needs more investigation: see the trufont.util.tracker module, and how it’s used in layer.paths.)

## Undo Manager API concepts

Flow of events when editing:

- An edit action is about to happen (for example the selection will be dragged)
- The undo manager is told the name of the operation (In this case “drag”, so the Undo menu can say “Undo drag” instead of just “Undo”)
- The undo manager is supplied with the current state of the data, which it will push onto the internal undo stack
- The edit action is handled (the user drags the selection)
- The undo manager is told the edit action is done (not sure this is even needed)
- The internal redo stack is cleared

Flow of events when the user does Undo:

- The undo manager is informed that will will perform an undo step. This allows to record subsequent edits into the redo stack: it will enter redo-mode.
- The undo manager is supplied with the current state of the data, which it will push onto the internal redo stack. If the previous action was another undo or a redo action, existing serialized data could be reused.
- The data of the state to be restored is popped off the undo stack, and applied to the live data
- The undo manager is informed that we’re done, allowing it to exit redo-mode

Flow of events when the user does Redo:

- The undo manager is informed that will will perform an redo step.
- The undo manager is supplied with the current state of the data, which it will push onto the internal undo stack
- The data of the state to be restored is popped off the redo stack, and applied to the live data
- The undo manager is informed that we’re done.

The undo manager should have methods to query its state:

- `canUndo()`
- `canRedo()`

Perhaps these methods should not return a boolean, but the operation name associated with the undo step. Or they could return a (flag, label) tuple. Or they should be separate methods, just like in NSUndoManager.

There may be a need to coalesce several undo steps into one, or to otherwise group several undo steps as if they are one.

## What to Undo

There is a need for distinct undo stacks for various items within a font. For example, each glyph should have its own undo manager, as each glyph more or less behaves as a separate document. If you edit glyph ‘a’, and then glyph ‘b’ and then switch back to glyph ‘a’, you want to be able to undo the latest edits to ‘a’.

Things get nicely complicated if we start thinking about glyph sets: is the action of deleting glyph ‘a’ part of glyph ‘a’s undo stack, or is there a separate undo stack for the glyph collection?

Here are some categories of font data that needs undo:

- Glyph/outline data, including metrics
- GlyphSet / Layer data (adding/removing glyphs)
- Font info data (should this be divided into sections? Eg. Naming vs. Vertical Metrics)
- Groups data
- Kerning data
- Feature data

## Undo vs wxWidgets

wxWidgets has support for undo via the wxCommandProcessor class. It largely seems to correspond to our proposed undo manager class. Still, I'm not convinced using this class will help us a lot, and that a Python implementation more targeted for our usage (while staying as abstract as practical) will be more flexible and efficient.

## Things to build

- The undo manager class
- An undo manager storage backend, allowing us to experiment with different storage strategies (naive in-memory, diffing in-memory, naive on-disk, diffing on-disk)
- A fast serializer for glyph objects, that includes selection info. The format should ideally be text, so we can leverage existing text diffing/patching tools. I think json would be a good candidate, especially since it’s already used in trufont for storage. Perhaps it can be built on top of the existing trufont json serializer

## Things to figure out

We need to identify all places in the GUI code that initiate edit actions, and analyze if things can be rearranged to make implementing undo as coherent and abstract as practical. Example actions:

- Dragging points
- Adding points/drawing
- Deleting points/contours
- Rearranging contours
- Changing starting point
- Applying path operations
- Slicing with the knife tool
- Using cut/copy/paste
- Applying undo/redo

## To Serialize or Not To Serialize

I’m not yet sure it will be necessary to store undo data on disk instead of in memory. Perhaps we should focus more on copyability of objects, rather than serializability. The undo manager could focus more on actions, and less on data.

## TruFont Qt Undo Manager

The previous generation of TruFont (based on Qt) has an undo manager written by Lasse Fister: github.com/trufont/trufont/blob/master/Lib/trufont/objects/undoManager.py
I don’t think this approach is abstract enough: this undo manager does work on glyphs, and has no abstraction beyond that.

## BlackFoundry Undo Manager

BlackFoundry started implementing Undo for TrueFont in their fork. So far it seems to work for most editing operations, but less so for drawing operations. This work is interesting and should be reviewed more carefully.

## Links & References

Cocoa’s undo manager is documented here:
<https://developer.apple.com/documentation/foundation/nsundomanager>

wxCommandProcessor class:
<https://docs.wxwidgets.org/3.1/classwx_command_processor.html>

BlackFoundry's fork:
<https://github.com/BlackFoundry/trufont/tree/wx-bf>
<https://github.com/BlackFoundry/tfont/tree/bf>

Efficient text diff/patch library:
<https://github.com/google/diff-match-patch>

Rope science (maybe relevant/useful for tracking changes in text):
<http://abishov.com/xi-editor/docs/rope_science_01.html>

Glitch Rewind version control, perhaps an inspiration?
<https://medium.com/glitch/reinventing-version-control-with-glitch-rewind-914c350da442>

Mercurial:
<https://www.mercurial-scm.org>
## Appendix & Related Topics

### Integrating undo mechanism with version control

A thought from Dave was that undo has some parallels with version control; the ‘real time fontforge collaboration’ feature he commissioned many years ago was based on the fontforge undo system. Paraphrasing: Does it make sense to try to leverage the similarities between undo mechanisms and version control mechanisms? Could an undo system be built on top of libraries that are designed for version control?

In my mind, git version control operates at a different granularity than “normal” editing, and therefore undo items do not correspond directly to commits. Also, undo items feel “volatile” in terms of UX, whereas git commits are meant to be there forever. Maybe I’m old school in this respect, so I’m open to arguments to the contrary. (But that’s not literally what Dave meant.)

Dave also mentioned mercurial could be interesting for this, as its all python; and perhaps also the "rope science" articles Raph wrote for the Xi text editor might also be relevant, along with the Xi undo system.

The Mercurial project should be studied for feasibility of using it for implementing undo or collaboration. Next step here is to find a good introduction on using the hg library outside of the Mercurial SCM.

###Real-time Collaboration

Some of the thoughts seem to go into the direction of real-time collaboration. Perhaps a good example of this is Google Docs: can such an approach work for font editing, and how should it be integrated into a tool such as TruFont?

On the one hand this could be a very exciting feature, on the other hand it calls for a very different approach to “old school” undo management. In other words: to implement for a desktop app is a very different scope than to implement a real-time collaboration feature.

Jérémie Hornus wrote: I think a real-time git commit (and more specifically push&pull) for each and every do action may be too slow and make the font editor unusable. However there could be some extra layer of information that could be shared (through version control) at some strategic action that concern more than one user. We are doing this for CJK font development at the moment enabling multiple users to work simultaneously on the same UFO.

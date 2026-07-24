# Birth and handover of a device

Primary reference: https://docs.pavona.org/book/doc/security/specs/device_provisioning/index.html

> Part intro: how a blank chip becomes a provisioned, owned device.

TODO: reuse the entity vocabulary from the 2021 CCSL talk's "OpenTitan
Identity Lifecycle" section (silicon creator, silicon owner, application
provider, end user; creator identity vs. owner identity), it was already
road-tested on a live audience. Also consider framing this Part as closing an
open question from that talk: it explicitly says "we have no clue where this
ROM comes from, where its code or key comes from" and leaves it unanswered.
This Part now has a concrete, simulatable answer via Egret personalization,
worth calling out narratively, possibly back-referenced from the
Introduction.

# ACARS message interpretation and UI design reference

This document records the interpretation of the October 12, 2026 ACARS log
and identifies information that could be useful in a future receiver UI.
The UI, storage model, and Pi 4 deployment have not yet been specified.
The UI ideas below are proposals, not implemented features.

See [ACARS UI visual references](acars-ui-reference.md) for locally saved
cockpit photographs and related presentation ideas.

## Evidence and scope

The fixed reference data is [acars_20261012.reference.jsonl](acars_20261012.reference.jsonl),
stored beside this document. **All line references below refer to this copy.**
It is a byte-for-byte snapshot of
`outputs/acars-macos-arm64/data/acars_20261012.jsonl` taken on October 12, 2026.
The original live log remains unchanged and can continue to grow.

The saved reference contains **478 records** (185,217 bytes).
The analysis below covers **lines 1–456**, the portion reviewed before the
snapshot was saved. Later records are retained as additional design and test
input; they are not included in the following statistics.

The reviewed portion contained:

- **456 records from 67 distinct aircraft registrations.**
- Reception from **October 11, 2026 at 8:09 p.m.** through **October 12, 2026
  at 7:01 p.m. Eastern**.
- **411 records with zero detected parity errors** and 45 with a nonzero
  parity-error count that the decoder corrected and accepted.
- **141 records with an empty message body**.

The filename uses the UTC date, which explains the October 11 evening records.
The reference copy is fixed; these counts describe its first 456 records.

Reference SHA-256:

```text
0788caf5224dedd91ae02780e4e82a2e47703d07cc6ee961231c5e2a8757ed8e
```

Use the reference as recorded input for offline design and testing, preserving
the original line order, timestamps, duplicates, and fragments. Replaying these
records must not make them appear to be new live receptions. The fixed reference
copy is intentionally included in Git for reproducible design and test input;
the original live log remains Git-ignored. This document contains selected
excerpts and interpretations.

Each JSON line represents a received **ACARS message block**. A block can
contain a complete message, a fragment of a longer report, or an acknowledgment.
Record counts therefore do not equal counts of complete reports or unique
events.

Interpretations fall into three levels:

1. **Directly readable:** explicit crew text, airport identifiers, coordinates,
   and values whose units are printed in the report.
2. **Defined by a protocol or decoder:** JSON field semantics, link status,
   and application identifiers such as `.ADS` or `.AT1`.
3. **Inferred or unresolved:** airline-specific layouts, proprietary numeric
   columns, and missing fragments. These must remain visibly qualified.

## JSON field reference

| Field | Meaning | UI implication |
|---|---|---|
| `timestamp` | Reception time as Unix seconds, including a fractional part. It can differ from an event time inside the message. | Show Eastern time by default, retain the UTC value, and distinguish reception time from report time. |
| `station_id` | Your receiver identifier, currently `MA-ACARS`. | Useful when combining data from multiple receivers later. |
| `channel` | Decoder channel index, starting at zero. | Use frequency as the main human-readable channel identifier. |
| `freq` | Radio frequency in MHz. | Support frequency filters and reception statistics. |
| `level`, `noise` | Relative signal and noise levels in dB; these are not calibrated dBm measurements. | Label them as relative levels and avoid implying calibrated signal strength or distance. |
| `error` | Detected parity errors before correction. Nonzero records in this log were corrected and accepted by the decoder. Zero does not exclude CRC-based corrections. | Show reception-quality information separately from the message's operational meaning. |
| `mode` | ACARS protocol mode, `2` in this snapshot. | This is not an ADS-B or transponder Mode S identifier. |
| `label` | Broad message type. Airline-specific messages also require inspecting `text`. | Classify using both label and payload, with an unknown category when needed. |
| `block_id` | Radio-link block identifier. Numeric identifiers in this file indicate aircraft-to-ground messages. | Preserve it for protocol inspection; it is not a flight identifier or report number. |
| `ack` | Technical acknowledgment. A string such as `"B"` acknowledges an earlier block B. `false` represents the NAK field. | Do not display `false` as an SDR decoding failure; it can occur on an unsolicited message. |
| `tail` | Aircraft registration/address as received. | Primary aircraft grouping field; retain its original spelling. |
| `flight` | Flight identifier transmitted by the aircraft's avionics. | Display it as received; do not assume it is always the marketed flight number or proof of the current operator. |
| `msgno` | Message sequence identifier, also used to associate fragments. | Retain the complete value and the fragment sequence. |
| `text` | Actual message payload. `\r\n` represents line breaks in JSON. | Provide a readable text view alongside the unchanged raw JSON. |
| `end` | In this decoder, `true` marks ETB: a block with more data to follow. | Use a derived name such as `more_blocks_follow`; do not label it “report complete.” |
| `depa`, `dsta` | Departure and destination airports extracted from recognized message formats. | Treat them as decoder-derived fields, not fields present in every transmission. |
| `app` | Decoder name and software version, added by the receiver. | Retain for provenance and troubleshooting. |

The `ack` and `end` behavior was checked against the pinned acarsdec JSON writer.
General ACARS headers and acknowledgments are described in
[Wavecom's ACARS documentation](https://www.wavecom.ch/content/ext/MonitoringSystemOnlineHelp/worddocuments/acars.htm).

## Message types present in the snapshot

| Label | Records | Information conveyed |
|---|---:|---|
| `H1` | 244 | Onboard-system messages: flight data, maintenance information, navigation reports, and requests. |
| `_d` | 108 | General responses, commonly acknowledgments. Empty bodies are expected. |
| `Q0` | 28 | Radio-link tests, rather than reports about flight conditions. |
| `SA` | 17 | Communications status: a link became available or was lost. |
| `15`, `16`, `12`, `22`, `1L` | 22 | In this log, mostly position, route, and flight-status reports in airline-specific formats. |
| `B6` | 9 | ADS-C reports and disconnect requests. |
| `BA` | 3 | Controller–pilot datalink messages or connection management. |
| `B9` | 9 | Requests for airport ATIS information. |
| `B0` | 1 | An air traffic services logon/notification message. |
| `5D`, `5U`, `5Z` | 4 | ATIS, weather, and airline-specific operational requests. |
| `10`, `20`, `24`, `30`, `32`, `Q7` | 6 | Company operational messages, including readable crew text. |
| `5V` | 5 | Empty messages here; the precise application purpose is not established by this log. |

These groups total 456 records. The grouped labels have the following individual
counts: `15`: 13, `16`: 5, `12`: 1, `22`: 2, `1L`: 1; `5D`: 1, `5U`: 1,
`5Z`: 2; and one each of `10`, `20`, `24`, `30`, `32`, and `Q7`.

Standard link-test and request labels are documented by decoder manufacturers.
Many numeric labels have airline-specific meanings, so a label alone should
not determine every field's interpretation. See
[Wavecom's examples](https://www.wavecom.ch/content/ext/MonitoringSystemOnlineHelp/worddocuments/acars.htm)
and [HOKA's label reference](https://www.hoka.it/oldweb/tech_info/systems/acarslabel.htm).

## Examples and interpretations

### Crew requesting a parking stand

**Line 342:** aircraft `G-VIIL`, transmitted flight identifier `BA0181`, label `10`.

```text
FTX01.JFKKOBA
HELLO ETA 1916Z
STAND PLEASE
```

The crew reports an expected arrival at **19:16 UTC / 3:16 p.m. Eastern**
and asks ground staff for its parking stand. This is a useful example of
plain-language operational messaging.

### Crew asking about turbulence

**Line 141:** aircraft `N809NW`, transmitted identifier `NW0047`, label `30`.

```text
121530 EHAM KJFK7
/FN 0047
A
WHAT IS THE TURB HEADING
INTO JFK ARE SEAT PROC
EDURUES BEING USED
```

The crew asks about turbulence approaching JFK and whether seating procedures
are being used. The surrounding text identifies an Amsterdam–JFK flight:
`EHAM` is Amsterdam Schiphol and `KJFK` is New York JFK.

Preserve `NW0047` as received. That identifier alone does not establish the
current operator; it should not automatically become an airline name in the UI.

### Explicit position and arrival report

**Line 193:** aircraft `OO-SFC`, header flight identifier `SN01CP`, label `12`.

```text
EBBR,KJFK,12OCT26,1622,165212
N 42.069,W 71.332,35066
KJFK04R,SN501
```

The directly readable information is:

- Route: **Brussels (`EBBR`) → New York JFK (`KJFK`)**.
- Date: **October 12, 2026**.
- Position: **42.069° N, 71.332° W**.
- JFK runway identifier: **04R**.
- The payload identifies flight `SN501`, while the header uses `SN01CP`.

The decoder also extracted `depa: "EBBR"` and `dsta: "KJFK"`.
The remaining numeric fields require the matching report layout before
assigning precise meanings and units. Compact coordinates in other formats
must not automatically be parsed the same way as these explicit decimal degrees.

### Flight management computer position and request messages

**Line 65:** aircraft `9V-SWH`, flight `SQ0026`, label `H1`.

```text
#M1BPOSN42027W071168,ASPEN,142147,340,PVD,142429,TRAIT,M42,25846,285/TS142147,121026C928
```

`M1` identifies the flight management computer (FMC). This report contains a
compact position, waypoint names `ASPEN`, `PVD`, and `TRAIT`, and associated
time fields. This can support a route/waypoint display once the layout is
verified.

Other FMC-related examples include:

- **Line 426, `OE-LPD` / `OS0038`:** a `REQPWI` message followed by
  `WQ390.380.370.350` and a transatlantic waypoint list. This is consistent
  with a **predicted wind information request**; that interpretation is
  inferred from the payload. The block has more data to follow.
- **Lines 241 and 444:** `#M2BPRG` reports containing destination/runway and
  flight-progress fields. Their remaining values need the applicable layout.

The `B` in the `#M1B` prefix is part of the sublabel framing; `M1` is the
two-character sublabel. See
[libacars' sublabel parsing guide](https://github.com/szpajder/libacars/blob/master/doc/PROG_GUIDE.md).

### Aircraft condition and hydraulic reports

**Line 5:** aircraft `N481UA`, flight `UA0487`, label `H1`, message `D32A`.

The body contains these explicit descriptors:

```text
#DFBA320,.../REP032,.../HYDRAULIC,REPORT,/...
FLIGHT.NUMBER,TRIGGER.REASON,FLIGHT.PHSAE
```

Later fragments, including **line 9**, contain:

```text
HTBLUE,HTGREEN,HTYELLOW,HPUMPB,HPUMPY,GHYDPB
```

This identifies a hydraulic-system report intended for ground monitoring or
maintenance analysis. Preserve the spelling `FLIGHT.PHSAE` as transmitted.
The column headings provide context, but they do not establish all numeric
scales or units.

Other `#DFB` reports contain repeated numeric samples, route identifiers,
and climb/descent markers. The long columns are structured flight-data
reports rather than ordinary prose. A matching aircraft/airline report layout
and the full set of fragments are needed to interpret them reliably.

The relevant `H1` sublabels identify onboard sources:

| Sublabel | Source and purpose |
|---|---|
| `DF` | Digital flight-data acquisition system; collects data from engines, controls, navigation, and other aircraft systems. |
| `CF` | Central fault/maintenance system; diagnostic and maintenance information. |
| `M1` | Flight management computer; navigation, flight planning, and related reports. |

These source identifiers are described in
[EUROCONTROL's datalink analysis](https://www.eurocontrol.int/sites/default/files/2025-07/eurocontrol-datalink-performance-and-capacity-analysis-v1-1.pdf).
Numeric report identifiers and other prefixes, including `#10B`, still require
their matching application layouts.

### Maintenance data with explicit units

**Line 389:** aircraft `N516GJ`, flight identifier `G74531`, label `H1`.

```text
APU TOT HOURS HISTORY  13471.0 HRS
APU CYCLES HISTORY       19020 CYC
```

Here the units are printed in the report: **13,471 APU operating hours** and
**19,020 cycles**. The APU is the auxiliary power unit. Adjacent fragments
contain engine-controller channel states and slat proximity-sensor states.

**Lines 317–318:** aircraft `N776AN`, flight `AA0199`, sends `#CFB` maintenance
fragments naming equipment such as:

```text
ELECTRONIC ENGINE CONTROLLER (EEC) (L ENG)
CENTRAL MAINTENANCE COMPUTING FUNCTION
AIR DATA INERTIAL REFERENCE UNIT
PRIMARY FLIGHT COMPUTER (LEFT)
APU FIRE DETECTION CARD
```

Diagnostic codes need the applicable maintenance documentation to establish
meaning and severity. A component name or code alone does not demonstrate a
component failure or an emergency. The UI should display the report faithfully
without inventing a severity level.

### Communications link changes

**Line 68:** aircraft `9V-SWH`, flight `SQ0026`, label `SA`.

```text
0LS142259V
```

This Media Advisory reports a **SATCOM link lost at 14:22:59 UTC**
(10:22:59 a.m. Eastern), with **VHF ACARS available**.

The format contains a version, established/lost state, affected link,
UTC time, and available links. For example, a body beginning `0EV...`
reports a **VHF link established**. These are aircraft communications events,
not receiver failures. Link codes and the format are defined by the
[libacars Media Advisory parser](https://github.com/szpajder/libacars/blob/master/libacars/media-adv.c).

### Encoded air traffic services messages

Several bodies contain application markers followed by hexadecimal payloads:

| Marker | Meaning |
|---|---|
| `.ADS` | ADS-C message: Automatic Dependent Surveillance–Contract. |
| `.DIS` | ADS-C disconnect request. |
| `.AT1` | FANS-1/A CPDLC message: Controller–Pilot Data Link Communications. |
| `.DR1` | CPDLC disconnect request. |

Examples include `B6` reports from `G-VIIF` and other aircraft, a `.DIS` request
from `EC-MKI` at lines 420–421, and `.AT1` messages from `EC-MOU` and `G-STBH`.

**ADS-C is distinct from the ADS-B feed.** These messages are carried over
ACARS, and their application payloads need an additional decoding layer.
ADS-C can convey aircraft position and flight status to ground systems;
CPDLC carries digital controller–pilot communications. See the
[FAA's data link guidance](https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.current/documentNumber/90-117).

The application identifiers are defined in
[libacars' ARINC parser](https://github.com/szpajder/libacars/blob/master/libacars/arinc.c).
The current receiver build omits `libacars`, so these payloads remain encoded
in the saved JSON. Supporting this decoding layer is a possible future
software change; it does not require a different radio for these captured
VHF ACARS messages.

## Fragmentation, repetition, and reception quality

### Continuation and missing blocks

The decoder writes `"end": true` when it sees **ETB**, an end-of-block marker
that indicates **more data follows**. This naming is counterintuitive. A final
text block uses ETX, and this JSON writer omits `end` in that case.

The hydraulic report includes `D32A`, `D32C`, `D32D`, and later fragments, but
some intervening blocks are missing from the snapshot. The common three-character
message prefix and final sequence character help associate these fragments.
Reassembly must also account for aircraft identity, label, reception time,
and identifier reuse.

Receiving a final fragment does not prove that all preceding fragments were
received. Any assembled view must identify gaps and retain links to its source
blocks. Repeated sublabel framing must be handled according to the message
format, rather than concatenating raw bodies blindly.

### Duplicate content

The snapshot contains repeated messages, including a few logged almost
simultaneously on different channels. Examples include:

- Lines **71–72**: the same `C-GLQJ` Media Advisory on 131.550 and 131.725 MHz.
- Lines **73–74**: the same aircraft's acknowledgment on those two channels.
- Lines **99–100**: a repeated position report from `N353QS`.

Repeated payloads can represent retries or repeated observations. Two log
records should not automatically become two separate flight events. The cause
of the simultaneous observations has not been established.

### Quality statistics

**411 of 456 blocks, approximately 90%, had zero detected parity errors.**
The remaining 45 were corrected and accepted. This supports successful
reception, but it does not measure missed transmissions, guarantee complete
reports, or establish a packet-loss rate. `error` is a decoder quality field,
not an aircraft fault indicator.

## Proposed UI considerations

These observations suggest the following design choices for later discussion:

1. **Aircraft timeline:** group observations by the received registration;
   retain flight identifiers as they change and allow different identifiers
   in headers and payloads.
2. **Message categories:** distinguish crew/company text, positions/routes,
   aircraft condition/maintenance reports, air traffic services, link events,
   acknowledgments, and unknown messages. Use label plus payload for classification.
3. **Readable details with raw access:** render actual line breaks, decoded
   fields, their units when known, and the unchanged JSON. Unknown bodies
   should remain useful to inspect.
4. **Time handling:** default to Eastern, offer UTC, and keep reception time
   separate from embedded report/event times. UTC filename dates must not be
   mistaken for Eastern calendar dates.
5. **Fragment-aware report view:** group related blocks, show missing sequences
   and completion evidence, and retain each original block. Derive a clear
   continuation field instead of exposing `end` as “complete.”
6. **Duplicate-aware presentation:** collapse repeated content in the main
   timeline when appropriate, while preserving observation counts, timestamps,
   frequencies, and raw records.
7. **Position provenance:** identify the source message and verified coordinate
   format for every map point. Do not assume every ACARS message contains a
   position or provides continuous tracking.
8. **Interpretation confidence:** distinguish explicit text, protocol-decoded
   fields, inferred meanings, and unresolved values. Assign proprietary numeric
   units only after obtaining a matching layout.
9. **Reception information:** keep signal/noise, parity corrections, frequency,
   station, and decoder version available without confusing them with aircraft
   maintenance or operational status.
10. **Additional application decoding:** evaluate `libacars` for ADS-C, CPDLC,
    and Media Advisory fields, preserving the original payload alongside any
    derived output.

The most immediately useful views would be a searchable message timeline,
an aircraft detail view, readable crew messages, and verified position reports.
Full maintenance interpretation depends on report layouts and complete
fragment reception.

# 7.2kV Assembly Data Audit vs RUS Bulletin 1728F-804 (April 2005)

Scope: `7200_A.csv`, `7200_B.csv`, `7200_C.csv` verified against
`UEP_Bulletin_1728F-804.pdf` ("Specifications and Drawings for 12.47/7.2 kV
Line Construction"), drawing index (Exhibit 4), assembly numbering format
(Exhibit 5), and the disposition-of-assemblies table (Exhibit 3).

## Confirmed correct

1. **Numbering format** matches Exhibit 5 exactly: `L1 N1 . N2` with
   category letters A (1-phase), B (2-phase), C (3-phase); subcategory
   semantics (1 tangent, 2 small angle, 3 suspension/large angle,
   4/5/6 deadends); crossarm identification ranges (11-19 single 8-ft,
   21-29 double 8-ft, 41-49 single 10-ft, 52+ 10-foot variants).
2. **`V` prefix semantics** confirmed: Exhibit 5 states the `V` prefix
   marks 24.9/14.4 kV assemblies, no prefix means 12.47/7.2 kV. The
   `14400_*.csv` tables and `voltage_family='14400'` implementation are
   consistent with the standard.
3. **Coverage**: 231 of 231 CSV assembly pairings map to real drawings in
   the bulletin (see exceptions below). All `Hin`/`Hout` values are
   internally consistent, radii/X positions present wherever heights are
   set, no duplicate names.
4. **Common dimensions verified against drawing OCR** (limited precision):
   - A1.1/A1.2 (page 17): single support tangent, spool neutral offset
     bracket — consistent with CSV (Phase1Hin=0 pin on pole top,
     NeutralHin=-42, GuyH1=-27).
   - C1.11/C1.12 (page 118): single crossarm 8-0" with 3'-8" pole-top
     spacing, pin-type insulators — CSV values (Phase1Hin=-5, center
     phase 9 in. above arms, NeutralHin=-42, GuyH1=-27) are consistent
     with a C1 tangent crossarm with center phase on the pole top.

## Discrepancies / items to review

| CSV entry | Bulletin says | Note |
|---|---|---|
| `7200_A`: `A6.22` | Only `A6.2` (feed-through deadend) and `A6.22G` (guide drawing, no materials) exist | `A6.22` is likely meant to be `A6.2` or the guide `A6.22G`; a materials assembly named `A6.22` is not in the bulletin index |
| `7200_B`: `B1.15,B2.25` | Bulletin lists `B2.24 (B1-1)` and `B2.25 (B1-1A)` as the tangent double-support-on-crossarms pair; `B1.15` does not exist in the bulletin | In-house pairing or typo; if in-house, consider an `AltName`-style note |
| `7200_B`: `B1.14,B2.24` | Bulletin `B1.14 (B9-1)` is "single support, neutral on crossarm", not the tangent double support | Same concern as above |
| `7200_C`: `C5.21L,C5.31L` inside the combined name `C5.21,C5.31,C5.21L,C5.31L,...` | Bulletin lists C5.21L/C5.31L as a separate large-conductor drawing (page 161) | Combined row mixes standard and large-conductor variants; heights may differ between the two drawings |
| `7200_C`: `C6.52G`,`C6.53G` | `G` suffix means **guide drawing (no materials)** per Exhibit 5 | Guide drawings should not be used as attachment assemblies; consider removing or flagging |

## Verified via OCR but not numerically confirmed

The RUS drawing pages are vector-traced text (no extractable text layer),
so dimension strings could only be spot-checked at low OCR confidence.
The following could not be verified number-by-number in this environment
and remain based on the original manual transcription:

- All `Phase*Hin`/`Phase*Hout` inch values
- `GuyH1..GuyH4` values
- `Radius`/`X` offsets

Recommend a human spot check of the drawings flagged above plus any
assembly used in production studies (the A1.11/C1.11 families used by
the test projects were checked and look consistent).

## Also loaded from the bulletins

- 1728F-803: Telecommunications (not yet used by polecad)
- 1728F-810/811: 34.5/46kV and 69kV (transmission) — the `34500_46000`
  and `69000` construction tables

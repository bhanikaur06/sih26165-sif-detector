import hashlib
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SIF_REPORTS = {
    "LSR_WAH": [
        "Rigger was found working on the monkey board without clipping his fall-arrest lanyard to the anchor point.",
        "Contractor climbed the flare stack ladder to change a beacon light without a harness or a work-at-height permit.",
        "Scaffold at the tank farm dyke was missing two guardrails on the top platform where painters were working.",
        "Electrician stood on the top rung of an unsecured ladder to access a junction box on the pump house roof.",
        "Insulation crew removed the toe boards from the process platform walkway and did not replace them before shift end.",
        "Worker was seen leaning over the open edge of the separator deck to retrieve a dropped spanner, with no edge protection in place.",
        "Roustabout used a stack of pallets instead of a certified ladder to reach the top of the crude storage tank.",
        "Two workers shared a single-person cage during a man-basket lift to inspect the flare tip.",
        "A rope access technician's harness lanyard was found frayed through more than half its diameter during a routine climb at the CTF roof.",
        "Housekeeping staff cleaning gutters on the GGS roof were not tied off and the roof access hatch had no barricade.",
        "A painter was observed standing on the handrail of the catwalk to reach a high spot on the vessel shell.",
    ],
    "LSR_LOF": [
        "A wrench slipped from the rig floor and fell past the cellar deck where two roughnecks were standing, narrowly missing them.",
        "High-pressure flowline connection was cracked open for maintenance while still showing residual pressure on the gauge, spraying fluid toward nearby workers.",
        "A wire rope sling parted under load during a pipe-handling job on the catwalk, sending the pipe rolling toward the crew.",
        "Operator stood directly under a suspended load while guiding a crane operator repositioning a separator skid.",
        "A pressure test plug blew out of a flowline fitting at the wellhead, striking the test rig frame a metre from the crew.",
        "Loose scaffold clamp fell from the third lift at the tank farm and landed near a walkway used by field staff.",
        "During pigging operations the pig launcher door was opened before the line was confirmed depressurised, and the door was thrown open by trapped pressure.",
        "A chain block failed while lifting a valve assembly, dropping the load onto the pipe rack below where a technician had been standing minutes earlier.",
        "Tubing was being racked back on the rig with workers standing in the direct line of the elevator swing.",
        "A grinding disc shattered during pipe-fitting work in the workshop, throwing fragments across the bay where a colleague was working unshielded.",
        "Crane was slewing a wellhead Christmas tree component over an occupied walkway instead of the designated barricaded lift path.",
    ],
    "LSR_CS": [
        "Two contractors entered the crude oil storage tank for cleaning without a valid confined space entry permit or forced ventilation running.",
        "Gas testing before entry into the separator vessel was skipped because the portable gas detector's battery was flat.",
        "A worker entered the mud pit to retrieve a dropped tool without a standby attendant posted at the entry point.",
        "Vessel entry for internal inspection proceeded although the isolation blinds on the inlet line had not been installed.",
        "Confined space entry into the wastewater sump was logged as complete, but the atmosphere had not been re-tested after a work break of over an hour.",
        "A fitter climbed into the GGS separator through the manway to clear a blockage while the vessel was still connected to the process header.",
        "Entry into the DG set fuel tank for repair work went ahead without continuous gas monitoring, relying only on the initial reading.",
        "Rescue equipment was not staged at the confined space entry point during tank cleaning at the CTF, despite it being listed on the permit.",
        "A helper was sent into the cellar deck sump to check a valve without checking that the area was free of accumulated hydrocarbon vapour.",
        "Vessel entry permit for the knockout drum was signed off by a supervisor who was not on site to verify pre-entry conditions.",
        "Worker entered a partially drained pipeline section to inspect welds without confirming the line had been purged of residual gas.",
    ],
    "LSR_ISO": [
        "Maintenance crew began dismantling a pump seal before confirming the motor's electrical isolation had been locked out at the breaker.",
        "A technician removed the guard on a rotating shaft while the equipment was only switched off at the local panel, not isolated and tagged.",
        "Valve on a flowline was opened for maintenance while an upstream isolation valve was left unlocked and was inadvertently reopened by another crew.",
        "Electrical panel was opened for fault-finding without verifying zero energy state with a tester, relying only on the breaker position.",
        "A worker removed his personal lock from a pump isolation point before confirming with the rest of the crew that all work was complete.",
        "Compressor was restarted from the control room while a mechanic was still inside the skid replacing a filter element.",
        "LOTO tags were applied to the wrong valve during a flowline tie-in, leaving the actual isolation point unlocked.",
        "Hydraulic power unit was not bled down before a hose was disconnected, causing a sudden release of stored pressure.",
        "A group lockbox for a shutdown job was opened and the equipment re-energised while two contractors were still working inside the vessel.",
        "Isolation of a heater's fuel gas line was confirmed verbally but the physical blind was never actually installed before hot work began nearby.",
        "Field operator bypassed the pump's isolation procedure to save time during a routine seal check, relying on the stop button alone.",
    ],
    "LSR_HW": [
        "Welding was carried out on a flowline support bracket without a valid hot work permit or a fire watch posted nearby.",
        "Cutting torch was used near the tank farm dyke where flammable vapour readings had not been checked beforehand.",
        "Grinding work on a pipe rack ignited nearby oil-soaked rags that had not been cleared from the area before the job started.",
        "A welder began arc welding on the separator platform while gas testing equipment at the site had expired its calibration.",
        "Hot work permit for repairs on the flare knockout drum was extended verbally past its validity without a fresh gas test.",
        "Sparks from a grinding job on the pipe rack landed near an open drum of solvent stored in the same bay.",
        "Welding continued on the wellhead cellar structure after the gas detector alarmed briefly, without stopping to re-verify the atmosphere.",
        "Fire watch assigned to a hot work job at the CTF left the area to attend another task while cutting work was still in progress.",
        "A cutting job on old pipework proceeded without confirming the line had been purged of residual crude, and vapour ignited briefly at the cut point.",
        "Hot work was carried out within the barricaded radius of an adjacent tank gauging operation without cross-checking the permit register.",
        "Portable grinder used near the mud pit threw sparks toward stacked wooden pallets that had not been moved clear of the hot work zone.",
    ],
    "LSR_LIFT": [
        "Crane lift of a wellhead component exceeded the rated capacity shown on the load chart for the boom angle in use.",
        "A tag line was not used while lifting a heavy valve assembly over the pipe rack, and the load swung into an adjacent structure.",
        "Sling angle during a skid lift at the GGS was outside the certified working limits, visibly overstressing the rigging.",
        "Lifting gear used to hoist a pump motor had a damaged shackle pin that was not identified during the pre-use inspection.",
        "Crane operator lifted a load over personnel working below on the rig floor instead of waiting for the area to be cleared.",
        "A makeshift lifting point welded to a skid frame was used for a crane lift without any engineering sign-off.",
        "Outriggers on the mobile crane were not fully extended on firm ground before a lift near the tank farm, and the crane tilted slightly under load.",
        "Lifting plan for the compressor package swap did not account for the ground bearing pressure near the excavation, and one outrigger pad sank during the lift.",
        "Banksman signals were not visible to the crane operator during a blind lift behind the workshop, and the load was set down off the marked position.",
        "A wire rope sling with visible broken strands was used to lift a separator internals basket out of the vessel.",
        "Two independent cranes were used for a tandem lift of a long pipe section without a documented lift plan coordinating their movements.",
    ],
    "LSR_DRV": [
        "Field supervisor's vehicle was travelling well above the site speed limit on the unpaved road between the wellpad and the GGS.",
        "Driver was found using a mobile phone while driving a crew bus between the staff colony and the field on a foggy morning.",
        "A light vehicle nearly collided head-on with a tanker on the narrow field road because neither driver slowed at the blind bend near the CTF.",
        "Seatbelts were not worn by two passengers in the rear seat of a pickup transporting crew to a remote wellhead.",
        "Driver showed clear signs of fatigue after a double shift but was still assigned to drive equipment back from the rig site at night.",
        "A loaded flatbed truck reversed toward the pipe rack without a spotter guiding it, coming within a metre of parked equipment.",
        "Vehicle brakes were reported as spongy during the pre-trip check but the truck was driven anyway to deliver chemicals to the field.",
        "Overloaded pickup carrying tools and personnel together lost traction on the muddy access road near the wellpad during monsoon.",
        "Driver overtook a tanker on a single-lane field road near the GGS junction with poor visibility ahead.",
        "A contractor drove a company vehicle off the designated route through an unmarked area close to an active flowline trench.",
    ],
    "LSR_BYP": [
        "High-level alarm on the separator was found silenced in the DCS with no corresponding work permit or management-of-change record.",
        "Relief valve on the flowline manifold was found gagged with a bolted flange, apparently to stop a persistent minor leak.",
        "Emergency shutdown pushbutton at the GGS was taped over after a previous false trip, disabling it without approval.",
        "Interlock preventing simultaneous operation of two valves was overridden in software during a shift without documenting the reason.",
        "Pressure safety valve isolation valve was left closed and locked after a calibration job, and the lock was never removed once work finished.",
        "Fire and gas detector in the pump house had been unplugged after repeated nuisance alarms and was never reconnected.",
        "A safety trip on the compressor was bypassed using a jumper wire to keep the unit running through a scheduled maintenance window.",
        "Guard interlock switch on a rotating equipment enclosure was taped down after operators found it inconvenient during routine checks.",
        "Level transmitter on the crude storage tank was found disconnected from the high-high trip logic, with the tank still being filled.",
        "Access door interlock on the electrical switchgear room was defeated with a wedge to allow it to be propped open during hot weather.",
    ],
    "LSR_PTW": [
        "Maintenance work on the wellhead choke began before the permit-to-work had been countersigned by the area authority.",
        "A hot work permit issued for the pipe rack was used to authorise unrelated confined space entry work at the same location.",
        "Contractor crew started excavation work near a buried flowline without a valid ground-disturbance permit or a line locate.",
        "Permit for electrical isolation work at the substation had expired at shift change but the crew continued working under the old permit.",
        "Work was carried out on the flare system using a permit written for a different, unrelated job at the CTF.",
        "A general work permit was used to cover live line tie-in work that should have required a separate high-risk permit.",
        "Isolation certificate referenced on the permit did not match the actual equipment being worked on at the GGS.",
        "Permit-to-work for tank cleaning was signed off by a supervisor without a site visit to verify pre-entry conditions.",
        "Work resumed after a shift handover without the incoming crew reviewing or re-validating the existing permit conditions.",
        "A verbal go-ahead was given to start pipeline tie-in work while the written permit was still pending final approval.",
    ],
    "LSR_GAS": [
        "H2S alarm at the wellhead sounded briefly during a routine check, and personnel in the area were not wearing their personal gas monitors.",
        "A minor flowline flange leak released gas near the wellpad, and the area was not immediately barricaded off from passing staff.",
        "Fixed gas detection system at the GGS control room showed a fault indication that had gone unresolved for several days.",
        "Crude oil vapour was detected near the tank farm gauging hatch at levels above the site action limit during routine monitoring.",
        "A pressure gauge on the separator inlet line showed erratic readings consistent with a possible internal leak, but the unit was not taken offline for inspection.",
        "Portable gas detector at the wellhead was found with an expired calibration sticker during a routine equipment check, and had been in use for two shifts.",
    ],
}

NON_SIF_REPORTS = {
    "NONSIF_HK": [
        "A small oil stain was noted on the workshop floor near the tool crib and was cleaned up before the shift ended.",
        "Waste bins near the field office were overflowing and needed to be emptied more frequently.",
        "Empty cable drums were left stacked untidily near the store, partially blocking a low-traffic walkway.",
        "A coil of unused rope was left coiled on the floor of the pump house instead of being hung on its rack.",
        "Housekeeping round found a few scattered nuts and bolts on the workbench in the electrical workshop.",
        "Paper records in the site office were found disorganised after the weekend and were refiled during the morning round.",
        "A used oil rag bin near the workshop entrance was slightly overfilled and was emptied as part of routine housekeeping.",
        "Grass along the perimeter fence near the staff colony had grown tall and was scheduled for trimming.",
        "A few empty water bottles were left on a desk in the control room after night shift and were removed the next morning.",
        "Signage pointing to the first-aid room in the admin block had faded and was flagged for repainting.",
        "A parking area near the main gate had a few potholes that were noted for the next maintenance round.",
        "Old cable ties and packaging material from a recent delivery were left near the store awaiting disposal.",
        "The noticeboard in the canteen had outdated safety posters that were due for replacement.",
        "A dust accumulation was noticed on top of the file cabinets in the site office during a routine inspection.",
        "Cones marking a minor pothole on the internal road were slightly displaced and were repositioned by the security guard.",
        "A leaking tap in the washroom near the workshop was reported and logged for the plumber to fix.",
        "A stack of empty cardboard boxes was left near the loading gantry office instead of being sent for recycling.",
        "The lawn sprinkler near the main gate garden was left running longer than needed one morning.",
        "A whiteboard in the shift handover room had notes from two weeks ago that had not been erased.",
        "Old tyre marks on the internal road near the workshop were flagged for a repaint of the lane markings.",
        "A small puddle of rainwater collected near a blocked drain outside the security cabin after overnight rain.",
        "The site library in the training room had a few outdated manuals that needed to be archived.",
    ],
    "NONSIF_PPE": [
        "A visitor in the admin building was seen without a hi-vis vest while walking through the non-operational office area.",
        "An office staff member briefly stepped into the yard without safety shoes to receive a courier delivery.",
        "A worker's hard hat sticker showing the last inspection date had faded and needed to be reissued.",
        "Safety glasses worn by a clerk in the stores area had a minor scratch and were replaced during the routine check.",
        "An employee was found wearing ear plugs of the wrong size for the low-noise office annex, where hearing protection is optional.",
        "A driver's high-visibility vest was slightly faded and was flagged for replacement at the next PPE issue.",
        "A worker in the covered warehouse was seen without gloves while sorting paperwork, a task that does not require them.",
        "PPE register in the store showed one pair of safety goggles overdue for return, with no incident linked to it.",
        "A canteen staff member was seen without a hairnet during a non-food-handling task in the storage area.",
        "A security guard's reflective armband was faded and was replaced during the weekly PPE check.",
        "An intern in the admin office wore open sandals briefly while moving between air-conditioned rooms, outside operational areas.",
        "A visitor's issued hard hat had a minor crack noted at the return counter and was withdrawn from circulation.",
        "A store clerk was found wearing a dust mask past its recommended usage hours during light paperwork duties.",
        "A driver's spare high-visibility vest kept in the vehicle glovebox was found slightly torn during a routine vehicle check.",
    ],
    "NONSIF_ERG": [
        "An office worker reported mild discomfort from sitting at a desk without an adjustable chair for extended periods.",
        "A clerk raised concerns about glare on the computer screen from the window in the afternoon.",
        "A control room operator mentioned that the chair armrest was loose and needed tightening.",
        "A worker in the stores mentioned the shelving was slightly too high for comfortable reach without a step stool.",
        "Staff in the site office requested better lighting at one of the desks near the printer.",
        "A radio operator reported that the headset was uncomfortable after long shifts and requested a replacement.",
        "An employee in the accounts office noted that the keyboard tray was positioned awkwardly for typing.",
        "A worker mentioned mild fatigue from standing for long periods at the reception counter.",
        "A store assistant suggested a footrest would help with prolonged standing at the issue counter.",
        "A technician in the instrumentation lab mentioned the workbench height was slightly low for comfortable use.",
        "A receptionist requested an anti-glare screen filter after noticing eye strain by late afternoon.",
        "A clerk in the records room asked for a rolling ladder instead of a step stool for reaching upper shelves.",
        "A driver mentioned the seat cushioning in one of the pool cars had worn thin over time.",
        "An operator in the control room suggested the desk lamp angle be adjusted to reduce screen glare.",
    ],
    "NONSIF_ADM": [
        "A training record for one contractor employee was found to be missing from the site induction file.",
        "The monthly safety meeting minutes for the admin block were not circulated on time.",
        "A visitor's log entry at the main gate was found incomplete, missing the exit time.",
        "An internal memo about the updated canteen timings had not been posted on the noticeboard yet.",
        "A routine fire extinguisher inspection tag in the admin office was overdue for renewal by two days.",
        "The site's emergency contact list posted in the reception area had one outdated phone number.",
        "A minor discrepancy was found between the attendance register and the gate entry log for one shift.",
        "The stationery register in the site office had not been updated for the past week.",
        "A scheduled toolbox talk in the administrative section was postponed due to a scheduling conflict.",
        "The suggestion box in the canteen had not been checked for over two weeks.",
        "A routine vehicle service record for a site sedan used for admin errands was filed a day late.",
        "The visitor badge return process at the gate was slightly delayed during a busy morning.",
        "A minor formatting error was found in the weekly non-operational activity report.",
        "The office pantry's drinking water dispenser needed its filter changed.",
        "A notice about a scheduled internet outage in the admin building was posted later than planned.",
        "A routine stationery stock count in the site office was completed a day behind schedule.",
        "A canteen feedback form summary for the previous month was submitted a few days past the deadline.",
        "The site newsletter draft for the admin block was delayed by one printing cycle.",
        "A minor mismatch was found between two copies of the leave register maintained in different offices.",
        "The reception desk's visitor pass numbering was found slightly out of sequence after a busy day.",
        "A scheduled software update for office computers in the admin block was postponed by a day.",
        "The site's lost-and-found register had one entry missing a description of the item.",
    ],
}

RANDOM_SEED = 7

CATEGORY_CONTEXT = {
    "LSR_WAH": ("Working at height", "PRODUCTION INSTALLATION"),
    "LSR_LOF": ("Well servicing / rig floor operations", "DRILLING RIG"),
    "LSR_CS": ("Vessel and tank entry", "PRODUCTION INSTALLATION"),
    "LSR_ISO": ("Machine maintenance", "WORKSHOP"),
    "LSR_HW": ("Hot work / welding and cutting", "PRODUCTION INSTALLATION"),
    "LSR_LIFT": ("Lifting and rigging", "DRILLING RIG"),
    "LSR_DRV": ("Vehicle movement and transport", "FIELD TRANSPORT"),
    "LSR_BYP": ("Process operations and control", "PRODUCTION INSTALLATION"),
    "LSR_PTW": ("Permit-controlled maintenance", "PRODUCTION INSTALLATION"),
    "LSR_GAS": ("Gas detection and monitoring", "WELLHEAD"),
    "NONSIF_HK": ("Housekeeping", "SUPPORT AREA"),
    "NONSIF_PPE": ("Handling supplies or material", "SUPPORT AREA"),
    "NONSIF_ERG": ("Office and administrative work", "OFFICE"),
    "NONSIF_ADM": ("Office and administrative work", "OFFICE"),
}

INSTALLATIONS = {
    "DRILLING RIG": [("RIG-07", "Drilling Services Contractor A"), ("RIG-12", "Drilling Services Contractor B")],
    "WELLHEAD": [("WELLPAD-14", "Field Operations North"), ("WELLPAD-23", "Field Operations South")],
    "PRODUCTION INSTALLATION": [("GGS-02", "Field Operations North"), ("GGS-05", "Field Operations South"), ("CTF-01", "Central Facilities")],
    "WORKSHOP": [("WKSHP-01", "Maintenance Services")],
    "FIELD TRANSPORT": [("TRANSPORT-01", "Logistics Contractor C")],
    "SUPPORT AREA": [("OCS-03", "Field Operations North"), ("STORE-01", "Central Facilities")],
    "OFFICE": [("ADMIN-01", "Central Facilities")],
}


def make_doc_id(category, index, text):
    key = f"{category}|{index}|{text}".encode("utf-8")
    digest = hashlib.sha1(key).hexdigest()[:10]
    return f"oil_{digest}"


def make_row(category, index, narrative, label):
    activity, subunit = CATEGORY_CONTEXT[category]
    installations = INSTALLATIONS[subunit]
    mine_id, operator_name = installations[index % len(installations)]
    return {
        "doc_id": make_doc_id(category, index, narrative),
        "narrative": narrative,
        "sif_label": label,
        "source_code": category,
        "split": "oil_validation",
        "mine_id": mine_id,
        "operator_name": operator_name,
        "activity": activity,
        "subunit": subunit,
    }


def build():
    rows = []
    for category, narratives in SIF_REPORTS.items():
        for i, narrative in enumerate(narratives):
            rows.append(make_row(category, i, narrative, 1))
    for category, narratives in NON_SIF_REPORTS.items():
        for i, narrative in enumerate(narratives):
            rows.append(make_row(category, i, narrative, 0))

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

    assert df["doc_id"].is_unique, "duplicate doc_id generated"
    assert df["narrative"].is_unique, "duplicate narrative text generated"
    assert 150 <= len(df) <= 200, f"row count {len(df)} outside 150-200 target"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "oil_validation.csv"
    df.to_csv(out_path, index=False)

    report = {
        "total_rows": int(len(df)),
        "label_balance": df["sif_label"].value_counts().to_dict(),
        "rows_per_category": df["source_code"].value_counts().to_dict(),
    }
    (PROCESSED_DIR / "oil_validation_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    build()

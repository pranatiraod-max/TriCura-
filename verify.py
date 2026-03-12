import json
import csv

class Patient:
    def __init__(self, pid, severity, arrival, treatment, specialization):
        self.patient_id = pid
        self.severity = int(severity)
        self.arrival_time = int(arrival)
        self.treatment_time = int(treatment)
        self.required_specialization = specialization

class Doctor:
    def __init__(self, did, spec):
        self.id = did
        self.spec = spec
        self.free_at = 0
        self.cur = None
        self.consec = 0
        self.rest_until = 0

def can_treat(d, p):
    return d.spec == "GENERAL" or d.spec == p.required_specialization

def score(p, t):
    return (p.severity ** 3) * 1000 + p.severity * (t - p.arrival_time) * 100

def avail(d, t, fc):
    return d.cur is None and d.free_at <= t and not (fc and d.rest_until > t)

def next_ev(after, rem, docs, fc):
    ts = [p.arrival_time for p in rem] + [d.free_at for d in docs]
    if fc:
        ts += [d.rest_until for d in docs]
    ts = [x for x in ts if x > after]
    return min(ts) if ts else None

def assign_all(t, ready, docs, done, tx, rests, fc):
    risk = 0
    changed = True
    while changed:
        changed = False
        waiting = sorted(
            [p for p in ready if p.patient_id not in done],
            key=lambda p: score(p, t),
            reverse=True
        )
        for p in waiting:
            if p.patient_id in done:
                continue
            eligible = [d for d in docs if avail(d, t, fc) and can_treat(d, p)]
            if not eligible:
                continue

            specialist = next((d for d in eligible if d.spec == p.required_specialization), None)
            general = next((d for d in eligible if d.spec == "GENERAL"), None)

            doc = None
            if specialist:
                doc = specialist
            elif general:
                spec_doc = next((d for d in docs if d.spec == p.required_specialization), None)
                if spec_doc:
                    wait_for_spec = max(
                        spec_doc.free_at,
                        spec_doc.rest_until if (fc and spec_doc.rest_until > t) else 0
                    ) - t
                else:
                    wait_for_spec = 999
                if p.severity >= 3 or wait_for_spec > 3:
                    doc = general

            if not doc:
                continue

            s = t
            e = s + p.treatment_time
            wait = s - p.arrival_time
            r = p.severity * wait
            risk += r

            doc.cur = p
            doc.free_at = e
            doc.consec += 1
            done.add(p.patient_id)
            ready.remove(p)

            if fc and e >= fc["after_min"] and doc.consec >= fc["limit"]:
                doc.rest_until = e + fc["rest"]
                doc.free_at = doc.rest_until
                doc.consec = 0
                rests.append({"doctor_id": doc.id, "start_time": e, "end_time": doc.rest_until})

            tx.append({
                "patient_id": p.patient_id,
                "doctor_id": doc.id,
                "start_time": s,
                "end_time": e
            })
            changed = True

    return risk

def scheduler(patients, fc=None):
    docs = [
        Doctor("Doctor_T", "TRAUMA"),
        Doctor("Doctor_C", "CARDIO"),
        Doctor("Doctor_G", "GENERAL"),
    ]

    rem = sorted(patients, key=lambda p: p.arrival_time)
    tx, rests, done = [], [], set()
    ready = []
    total_risk = 0
    t = 0

    while len(done) < len(patients):
        still = []
        for p in rem:
            if p.arrival_time <= t:
                ready.append(p)
            else:
                still.append(p)
        rem = still

        for d in docs:
            if d.cur and d.free_at <= t:
                d.cur = None

        total_risk += assign_all(t, ready, docs, done, tx, rests, fc)

        nxt = next_ev(t, rem, docs, fc)
        if nxt is None:
            break
        t = nxt

    tx.sort(key=lambda x: x["start_time"])
    return {"treatments": tx, "estimated_total_risk": total_risk, "rests": rests}


if __name__ == "__main__":
    patients = []
    with open("triage_sample.csv", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            patients.append(Patient(
                pid=row["patient_id"],
                severity=row["severity"],
                arrival=row["arrival_time"],
                treatment=row["treatment_time"],
                specialization=row["required_specialization"]
            ))

    result = scheduler(patients, fc=None)

    with open("submission.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Done! Output written to submission.json")
    print(json.dumps(result, indent=2))
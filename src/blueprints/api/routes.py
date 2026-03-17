




@app.get("/api/next_arrival")
def next_arrival():
    stop_code = request.args.get("stop_id", "").strip()
    bus_number = request.args.get("bus_number", "").strip()

    if not stop_code or not bus_number:
        return jsonify({"error": "stop_id and bus_number are required"}), 400

    stop_id = STOPCODE_TO_STOPID.get(stop_code)
    if not stop_id:
        return jsonify({"error": f"unknown stop_code: {stop_code}"}), 400

    route_id_needed = SHORT_TO_ROUTEID.get(bus_number)
    if not route_id_needed:
        return jsonify({"error": f"unknown route_short_name: {bus_number}"}), 400

    resp = requests.get(GTFS_TRIP_URL, timeout=10)
    resp.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)

    now = int(time.time())
    best = None

    for ent in feed.entity:
        if not ent.HasField("trip_update"):
            continue

        tu = ent.trip_update
        route_id = tu.trip.route_id if tu.trip.HasField("route_id") else None
        if route_id != route_id_needed:
            continue

        trip_id = tu.trip.trip_id if tu.trip.HasField("trip_id") else None

        for stu in tu.stop_time_update:
            if stu.stop_id != stop_id:
                continue

            eta_unix = None
            if stu.HasField("arrival") and stu.arrival.time:
                eta_unix = int(stu.arrival.time)
            elif stu.HasField("departure") and stu.departure.time:
                eta_unix = int(stu.departure.time)

            if eta_unix is None or eta_unix < now:
                continue

            if best is None or eta_unix < best[0]:
                best = (eta_unix, trip_id, route_id)

    if best is None:
        return jsonify({
            "stop_code": stop_code,
            "stop_id": stop_id,
            "bus_number": bus_number,
            "route_id": route_id_needed,
            "next_arrival": None
        })

    eta_unix, trip_id, route_id = best
    return jsonify({
        "stop_code": stop_code,
        "stop_id": stop_id,
        "bus_number": bus_number,
        "route_id": route_id_needed,
        "next_arrival": {
            "eta_unix": eta_unix,
            "eta_seconds": eta_unix - now,
            "eta_minutes": round((eta_unix - now) / 60.0, 1),
            "trip_id": trip_id,
            "route_id": route_id
        }
    })

@app.get("/api/shape")
def get_shape():
    stop_id = request.args.get("stop_id", "").strip()
    trip_id = request.args.get("trip_id", "").strip()
    direction = request.args.get("direction", "").strip()
    if stop_id:
        with open("./data/stop_times.txt", "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if str((row.get("stop_id")).strip()) == str(stop_id):
                    trip_id = (row.get("trip_id")).strip()
                    break

    with open("./data/trips.txt", "r", encoding="utf-8-sig", newline="") as f:
        shape_id = None;
        for row in csv.DictReader(f):
            if str((row.get("trip_id")).strip()) == str(trip_id):
                shape_id = (row.get("shape_id")).strip()
                with open("./data/shapes.txt", "r", encoding="utf-8-sig", newline="") as g:
                    shape_pts = []
                    for row in csv.DictReader(g):
                        if (row.get("shape_id") or "").strip() == shape_id:
                            seq = int((row.get("shape_pt_sequence") or "").strip())
                            lon = float((row.get("shape_pt_lon") or "").strip())
                            lat = float((row.get("shape_pt_lat") or "").strip())
                            shape_pts.append([seq, lon, lat])
                    shape_pts.sort()
                    for i in shape_pts:
                        i.pop(0)
                    # send features to json
                    return jsonify(
                        {
                            "type": "FeatureCollection",
                            "features": [{
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": shape_pts,
                                },
                                "properties": {},
                            }],
                        }
                    )
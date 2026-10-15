// Development tool (not published): search camera angles for the midway tour stops and the stage views that clip
// least with their surroundings. Load the page at a stop (#w3-build or #w3), then in the console:
//   const cs = await import('/dev/camera_search.js'); cs.searchStop(window.__au6, stop)
// A candidate camera (az / el / dist around the current one) is scored on:
//   - obstruction: share of 13 sight lines to the focus area blocked by model geometry (roofs and tree crowns, which
//     the viewer fades anyway, count less);
//   - clearance: any geometry within 1.5 m of the camera (it would cut through the near plane);
//   - inside: the first surface on the way to the focus is a back face (the camera sits inside a building);
//   - change: how far it moves from the current framing (so a stop keeps its composition when it is already fine).
const OVERHEAD = /Tree_Crowns|Corrugated_Roofs|Polycarbonate_Roof|WC_Entrance_Canopy|Street_Trees|Roof/;

function visibleDeep(o) { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; }

export function scoreView(a, F, v, base, meshes) {
  const { THREE } = a;
  const view = a.viewFrom(F, v), C = view.pos;
  if (C.y < 1.5) return { score: Infinity };
  const rc = new THREE.Raycaster(); rc.firstHitOnly = true;
  // sight lines: the focus, and a ring 1.8 m round it at knee and head height
  const targets = [F.clone()];
  for (let i = 0; i < 6; i++) {
    const ang = i / 6 * Math.PI * 2;
    for (const y of [0.6, 1.6]) targets.push(new THREE.Vector3(F.x + Math.cos(ang) * 1.8, y, F.z + Math.sin(ang) * 1.8));
  }
  let blocked = 0, inside = 0;
  targets.forEach((P, i) => {
    const dir = P.clone().sub(C), d = dir.length(); dir.divideScalar(d);
    rc.set(C, dir); rc.far = d - 0.25;
    const h = rc.intersectObjects(meshes, false)[0];
    if (!h) return;
    blocked += OVERHEAD.test(h.object.userData.layer || '') ? 0.4 : 1;
    if (i === 0 && h.face && h.face.normal.dot(dir) > 0.05) inside = 1;   // looking out through a back face
  });
  // clearance round the camera
  let near = 0;
  const dirs = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1],[1,1,1],[1,1,-1],[1,-1,1],[1,-1,-1],[-1,1,1],[-1,1,-1],[-1,-1,1],[-1,-1,-1]];
  for (const [x, y, z] of dirs) {
    rc.set(C, new THREE.Vector3(x, y, z).normalize()); rc.far = 1.5;
    if (rc.intersectObjects(meshes, false).length) { near = 1; break; }
  }
  const dAz = Math.abs(((v.az - base.az + 540) % 360) - 180), change = 0.004 * dAz + 0.01 * Math.abs(v.el - base.el) + 0.03 * Math.abs(v.dist - base.dist);
  const obstruction = blocked / targets.length;
  return { score: 10 * obstruction + 30 * near + 100 * inside + change, obstruction: +obstruction.toFixed(2), near, inside };
}

export function searchStop(a, stop, focusY = 1.0) {
  const { THREE } = a;
  a.camera.aspect = 1.6; a.camera.updateProjectionMatrix();          // landscape: viewFrom's portrait stretch off
  const F = a.snTo3(stop.focus[0], stop.focus[1], focusY);
  const meshes = a.xrayCandidates.filter(visibleDeep);
  const base = { az: stop.az, el: stop.el, dist: stop.dist };
  const before = scoreView(a, F, base, base, meshes);
  let best = { ...base, ...before };
  for (const dAz of [-90, -60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60, 90])
    for (const el of [...new Set([base.el, base.el - 10, base.el + 10, base.el + 20].map(e => Math.min(75, Math.max(12, e))))])
      for (const dist of [base.dist, Math.round(base.dist * 1.15), Math.round(base.dist * 1.3)]) {
        const v = { az: ((base.az + dAz + 540) % 360) - 180, el, dist };
        const r = scoreView(a, F, v, base, meshes);
        if (r.score < best.score) best = { ...v, ...r };
      }
  if (best.score > 5)                                               // still poor: look all round, steeper, further out
    for (let az = -180; az < 180; az += 15)
      for (const el of [20, 30, 40, 50, 60, 70, 80])
        for (const k of [0.8, 1, 1.2, 1.4]) {
          const v = { az, el, dist: Math.round(base.dist * k) };
          const r = scoreView(a, F, v, base, meshes);
          if (r.score < best.score) best = { ...v, ...r };
        }
  return { label: stop.label, before: { ...base, ...before }, after: best };
}

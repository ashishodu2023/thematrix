/**
 * Operator Console 3D HUD — meters, branch graph, faction tug, EMP core.
 * Uses local Three.js (no CDN).
 */
import * as THREE from "/static/vendor/three/three.module.js";

function mkRenderer(canvas, clearAlpha = 0.15) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  r.setClearColor(0x010302, clearAlpha);
  return r;
}

function fit(renderer, camera, canvas) {
  const parent = canvas.parentElement || canvas;
  const w = Math.max(120, parent.clientWidth || canvas.clientWidth || 320);
  const h = Math.max(100, parent.clientHeight || canvas.clientHeight || 140);
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  return { w, h };
}

function labelSprite(text, color = "#7CFF7C") {
  const c = document.createElement("canvas");
  c.width = 256;
  c.height = 64;
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgba(1,8,3,0.55)";
  ctx.fillRect(0, 12, 256, 40);
  ctx.font = "600 22px monospace";
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(text).slice(0, 18), 128, 32);
  const tex = new THREE.CanvasTexture(c);
  const spr = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  spr.scale.set(2.4, 0.6, 1);
  return spr;
}

/* ——— METERS (4 towers) ——— */
let meters = null;

export function initMeters3D(canvas) {
  if (meters) return meters;
  const renderer = mkRenderer(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 5.5, 11);
  camera.lookAt(0, 2, 0);
  scene.add(new THREE.AmbientLight(0x39ff14, 0.45));
  const key = new THREE.DirectionalLight(0x7cff7c, 1.0);
  key.position.set(4, 10, 6);
  scene.add(key);

  const colors = [0x39ff14, 0xffd54f, 0x80deea, 0x7cff7c];
  const names = ["TRACE", "THREAT", "TRAIN", "TICK"];
  const towers = [];
  for (let i = 0; i < 4; i++) {
    const g = new THREE.Group();
    const base = new THREE.Mesh(
      new THREE.CylinderGeometry(0.55, 0.65, 0.25, 12),
      new THREE.MeshStandardMaterial({ color: 0x062010, emissive: 0x0a2a14, emissiveIntensity: 0.3 })
    );
    base.position.y = 0.12;
    const fill = new THREE.Mesh(
      new THREE.CylinderGeometry(0.42, 0.42, 1, 16),
      new THREE.MeshStandardMaterial({
        color: colors[i],
        emissive: colors[i],
        emissiveIntensity: 0.55,
        transparent: true,
        opacity: 0.9,
      })
    );
    fill.position.y = 0.5;
    fill.scale.y = 0.05;
    const shell = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.CylinderGeometry(0.48, 0.48, 4.2, 12)),
      new THREE.LineBasicMaterial({ color: colors[i], transparent: true, opacity: 0.35 })
    );
    shell.position.y = 2.2;
    const lab = labelSprite(names[i], i === 1 ? "#ffd54f" : "#7CFF7C");
    lab.position.set(0, 4.7, 0);
    g.add(base, fill, shell, lab);
    g.position.x = (i - 1.5) * 2.6;
    scene.add(g);
    towers.push({ fill, color: colors[i], value: 0, target: 0 });
  }

  const grid = new THREE.GridHelper(14, 14, 0x1f6b2e, 0x0a2a14);
  grid.position.y = 0;
  scene.add(grid);

  meters = { renderer, scene, camera, canvas, towers, t: 0 };
  const loop = () => {
    requestAnimationFrame(loop);
    meters.t += 0.016;
    for (const tw of meters.towers) {
      tw.value += (tw.target - tw.value) * 0.12;
      const h = Math.max(0.08, tw.value * 4.0);
      tw.fill.scale.y = h;
      tw.fill.position.y = h / 2 + 0.15;
      tw.fill.material.emissiveIntensity = 0.4 + tw.value * 0.5 + Math.sin(meters.t * 3) * 0.05;
    }
    fit(renderer, camera, canvas);
    renderer.render(scene, camera);
  };
  loop();
  window.addEventListener("resize", () => fit(renderer, camera, canvas));
  return meters;
}

export function updateMeters3D({ trace = 0, threat = 0, train = 0, tick = 0 } = {}) {
  if (!meters) return;
  meters.towers[0].target = Math.min(1, Number(trace) / 100);
  meters.towers[1].target = Math.min(1, Number(threat) / 10);
  meters.towers[2].target = Math.min(1, Number(train) / 20);
  meters.towers[3].target = Math.min(1, (Number(tick) % 20) / 20);
}

/* ——— BRANCH GRAPH ——— */
let branchHud = null;

export function initBranch3D(canvas) {
  if (branchHud) return branchHud;
  const renderer = mkRenderer(canvas, 0.12);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 8, 14);
  camera.lookAt(0, 0, 0);
  scene.add(new THREE.AmbientLight(0x39ff14, 0.5));
  const root = new THREE.Group();
  scene.add(root);
  branchHud = { renderer, scene, camera, canvas, root, nodes: new Map(), edges: null, t: 0 };

  const loop = () => {
    requestAnimationFrame(loop);
    branchHud.t += 0.016;
    root.rotation.y = Math.sin(branchHud.t * 0.25) * 0.12;
    for (const n of branchHud.nodes.values()) {
      if (n.userData.pulse) {
        const s = 1 + Math.sin(branchHud.t * 3) * 0.08;
        n.scale.setScalar(s);
      }
    }
    fit(renderer, camera, canvas);
    renderer.render(scene, camera);
  };
  loop();
  window.addEventListener("resize", () => fit(renderer, camera, canvas));
  return branchHud;
}

export function updateBranch3D(branch) {
  if (!branchHud) return;
  const nodes = branch?.nodes || [];
  const path = branch?.path || [];
  const cur = branch?.current || "";
  const predicted = branch?.predicted || "";
  const taken = new Set(path);

  while (branchHud.root.children.length) {
    const c = branchHud.root.children.pop();
    c.geometry?.dispose?.();
    c.material?.dispose?.();
  }
  branchHud.nodes.clear();

  const show = nodes.length ? nodes : [{ id: "idle", label: "…", state: "idle", next: [] }];
  const n = show.length;
  const cols = Math.min(5, Math.ceil(Math.sqrt(n)));
  const rows = Math.ceil(n / cols);

  show.forEach((meta, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const x = (col - (cols - 1) / 2) * 2.8;
    const z = (row - (rows - 1) / 2) * 2.6;
    let color = 0x1f6b2e;
    let pulse = false;
    if (meta.id === cur || meta.state === "current") {
      color = 0x39ff14;
      pulse = true;
    } else if (meta.id === predicted || meta.state === "predicted") color = 0xffd54f;
    else if (taken.has(meta.id) || meta.state === "taken") color = 0x7cff7c;
    else if (meta.state === "ahead") color = 0x80deea;

    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(1.4, meta.fork ? 1.1 : 0.7, 1.4),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: pulse ? 0.7 : 0.35,
        transparent: true,
        opacity: 0.92,
      })
    );
    mesh.position.set(x, meta.fork ? 0.7 : 0.4, z);
    mesh.userData = { pulse, id: meta.id };
    const lab = labelSprite(meta.label || meta.id, pulse ? "#b4ffb4" : "#7CFF7C");
    lab.position.set(x, mesh.position.y + 1.1, z);
    branchHud.root.add(mesh, lab);
    branchHud.nodes.set(meta.id, mesh);
  });

  // edges
  const pts = [];
  for (const meta of show) {
    const from = branchHud.nodes.get(meta.id);
    if (!from) continue;
    for (const dst of meta.next || []) {
      const to = branchHud.nodes.get(dst);
      if (!to) continue;
      pts.push(from.position.x, from.position.y, from.position.z, to.position.x, to.position.y, to.position.z);
    }
  }
  if (pts.length) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    branchHud.root.add(
      new THREE.LineSegments(geo, new THREE.LineBasicMaterial({ color: 0x1f6b2e, transparent: true, opacity: 0.65 }))
    );
  }
}

/* ——— FACTION TUG ——— */
let faction = null;

export function initFaction3D(canvas) {
  if (faction) return faction;
  const renderer = mkRenderer(canvas, 0.12);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50);
  camera.position.set(0, 4, 9);
  camera.lookAt(0, 0.5, 0);
  scene.add(new THREE.AmbientLight(0xffffff, 0.35));
  const sun = new THREE.DirectionalLight(0x39ff14, 0.8);
  sun.position.set(3, 5, 2);
  scene.add(sun);

  const beam = new THREE.Mesh(
    new THREE.BoxGeometry(8, 0.2, 0.5),
    new THREE.MeshStandardMaterial({ color: 0x0a2814, emissive: 0x145c28, emissiveIntensity: 0.3 })
  );
  beam.position.y = 1.2;
  const pivot = new THREE.Group();
  pivot.add(beam);

  const zion = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 16, 16),
    new THREE.MeshStandardMaterial({ color: 0x39ff14, emissive: 0x39ff14, emissiveIntensity: 0.7 })
  );
  zion.position.set(-3.2, 0.9, 0);
  const agents = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 16, 16),
    new THREE.MeshStandardMaterial({ color: 0xff3b4e, emissive: 0xff3b4e, emissiveIntensity: 0.7 })
  );
  agents.position.set(3.2, 0.9, 0);
  pivot.add(zion, agents);

  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.35, 0.6, 1.4, 8),
    new THREE.MeshStandardMaterial({ color: 0x062010, wireframe: true })
  );
  base.position.y = 0.3;
  scene.add(base, pivot);
  const lz = labelSprite("ZION", "#39FF14");
  lz.position.set(-3.2, 2.4, 0);
  const la = labelSprite("AGENTS", "#ff3b4e");
  la.position.set(3.2, 2.4, 0);
  scene.add(lz, la);

  faction = { renderer, scene, camera, canvas, pivot, ratio: 0.5, t: 0 };
  const loop = () => {
    requestAnimationFrame(loop);
    faction.t += 0.016;
    const tilt = (faction.ratio - 0.5) * 0.7;
    faction.pivot.rotation.z += (tilt - faction.pivot.rotation.z) * 0.1;
    faction.pivot.position.y = 0.05 * Math.sin(faction.t * 2);
    fit(renderer, camera, canvas);
    renderer.render(scene, camera);
  };
  loop();
  window.addEventListener("resize", () => fit(renderer, camera, canvas));
  return faction;
}

export function updateFaction3D({ zion = 0, agents = 0 } = {}) {
  if (!faction) return;
  const tot = Math.max(1, Number(zion) + Number(agents));
  faction.ratio = Number(zion) / tot;
}

/* ——— EMP CORE ——— */
let emp = null;

export function initEmp3D(canvas) {
  if (emp) return emp;
  const renderer = mkRenderer(canvas, 0.1);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 40);
  camera.position.set(0, 2.2, 5.5);
  camera.lookAt(0, 0.6, 0);
  scene.add(new THREE.AmbientLight(0x39ff14, 0.4));
  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(1.0, 1),
    new THREE.MeshStandardMaterial({
      color: 0xffd54f,
      emissive: 0xff3b4e,
      emissiveIntensity: 0.5,
      wireframe: true,
    })
  );
  const shell = new THREE.Mesh(
    new THREE.IcosahedronGeometry(1.35, 0),
    new THREE.MeshBasicMaterial({ color: 0x39ff14, wireframe: true, transparent: true, opacity: 0.25 })
  );
  scene.add(core, shell);
  emp = { renderer, scene, camera, canvas, core, shell, heat: 0.4, alive: true, t: 0 };
  const loop = () => {
    requestAnimationFrame(loop);
    emp.t += 0.016;
    const h = emp.heat;
    emp.core.rotation.y += 0.01 + h * 0.04;
    emp.core.rotation.x += 0.006;
    emp.shell.rotation.y -= 0.008;
    const scale = 0.85 + h * 0.5 + (emp.alive ? Math.sin(emp.t * 4) * 0.03 : 0);
    emp.core.scale.setScalar(scale);
    emp.core.material.emissiveIntensity = 0.3 + h * 0.9;
    emp.core.material.color.setHex(h > 0.75 ? 0xff3b4e : h > 0.45 ? 0xffd54f : 0x39ff14);
    fit(renderer, camera, canvas);
    renderer.render(scene, camera);
  };
  loop();
  window.addEventListener("resize", () => fit(renderer, camera, canvas));
  return emp;
}

export function updateEmp3D({ heat = 40, alive = true } = {}) {
  if (!emp) return;
  emp.heat = Math.min(1, Math.max(0, Number(heat) / 100));
  emp.alive = alive !== false;
}

export function bootAllHud(canvases) {
  if (canvases.meters) initMeters3D(canvases.meters);
  if (canvases.branch) initBranch3D(canvases.branch);
  if (canvases.faction) initFaction3D(canvases.faction);
  if (canvases.emp) initEmp3D(canvases.emp);
}

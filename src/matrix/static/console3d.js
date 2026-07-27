/**
 * Mega City 3D — Three.js Operator map.
 * Drag orbit · scroll zoom · click sector · dbl-click move
 */
import * as THREE from "/static/vendor/three/three.module.js";
import { OrbitControls } from "/static/vendor/three/examples/jsm/controls/OrbitControls.js";

const CITY_XY = {
  jack_point: [14, 78],
  apartment: [30, 52],
  club: [46, 70],
  club_vip: [52, 58],
  keymaker_hall: [70, 62],
  oracle_apartment: [34, 24],
  cafe: [58, 40],
  hotel_lobby: [62, 74],
  subway: [74, 54],
  rooftop: [82, 22],
  highway: [90, 66],
  construct: [16, 16],
  nebuchadnezzar: [8, 36],
  zion_dock: [4, 48],
  real_world: [8, 8],
};

const EDGES = [
  ["jack_point", "apartment"],
  ["jack_point", "subway"],
  ["jack_point", "hotel_lobby"],
  ["apartment", "club"],
  ["apartment", "oracle_apartment"],
  ["club", "cafe"],
  ["club", "hotel_lobby"],
  ["club", "club_vip"],
  ["club_vip", "keymaker_hall"],
  ["keymaker_hall", "hotel_lobby"],
  ["oracle_apartment", "cafe"],
  ["cafe", "subway"],
  ["hotel_lobby", "rooftop"],
  ["hotel_lobby", "subway"],
  ["subway", "highway"],
  ["rooftop", "highway"],
  ["construct", "nebuchadnezzar"],
  ["nebuchadnezzar", "real_world"],
  ["nebuchadnezzar", "zion_dock"],
];

const OUT = new Set(["construct", "nebuchadnezzar", "zion_dock", "real_world"]);

function toWorld(id) {
  const [px, py] = CITY_XY[id] || [50, 50];
  // percent → world XZ
  const x = (px - 50) * 0.42;
  const z = (py - 50) * 0.42;
  return new THREE.Vector3(x, 0, z);
}

function buildingHeight(id) {
  if (OUT.has(id)) return 1.2 + (id === "nebuchadnezzar" ? 2.2 : 0.6);
  if (id === "rooftop") return 7.5;
  if (id === "hotel_lobby") return 6.2;
  if (id === "highway") return 1.4;
  if (id === "subway") return 1.8;
  return 2.8 + ((id.length * 17) % 40) / 10;
}

let renderer, scene, camera, controls, root, raycaster, pointer;
let buildings = new Map();
let agentsRoot;
let huntLine;
let labelSprites = new Map();
let animId = 0;
let selectedId = null;
let lastSig = "";
let onSelect = () => {};
let onMove = () => {};
let ready = false;

function makeLabel(text) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 256, 64);
  ctx.fillStyle = "rgba(1,8,3,0.72)";
  ctx.fillRect(8, 12, 240, 40);
  ctx.strokeStyle = "rgba(57,255,20,0.55)";
  ctx.strokeRect(8, 12, 240, 40);
  ctx.font = "600 22px monospace";
  ctx.fillStyle = "#7CFF7C";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(text).slice(0, 18), 128, 32);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  const mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false });
  const spr = new THREE.Sprite(mat);
  spr.scale.set(4.2, 1.05, 1);
  return spr;
}

function addGridCity() {
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(64, 64),
    new THREE.MeshStandardMaterial({
      color: 0x031008,
      roughness: 0.92,
      metalness: 0.05,
      transparent: true,
      opacity: 0.95,
    })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  root.add(ground);

  const grid = new THREE.GridHelper(64, 64, 0x1f6b2e, 0x0a2a14);
  grid.position.y = 0.02;
  root.add(grid);

  // Dense Mega City blocks — streets + towers (atmosphere)
  const blockMat = new THREE.MeshStandardMaterial({
    color: 0x051a0c,
    emissive: 0x0a2e14,
    emissiveIntensity: 0.1,
    roughness: 0.88,
  });
  for (let gx = -5; gx <= 5; gx++) {
    for (let gz = -5; gz <= 5; gz++) {
      if (Math.abs(gx) < 1 && Math.abs(gz) < 1) continue;
      const h = 1.2 + ((Math.abs(gx * 17 + gz * 31) % 50) / 10) * 1.4;
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(2.2, h, 2.2),
        blockMat.clone()
      );
      box.material.emissiveIntensity = 0.06 + (h / 20);
      box.position.set(gx * 4.2, h / 2, gz * 4.2);
      root.add(box);
      // street neon strip
      if (gx % 2 === 0) {
        const neon = new THREE.Mesh(
          new THREE.BoxGeometry(0.08, 0.06, 3.6),
          new THREE.MeshBasicMaterial({ color: 0x39ff14, transparent: true, opacity: 0.35 })
        );
        neon.position.set(gx * 4.2 + 1.3, 0.08, gz * 4.2);
        root.add(neon);
      }
    }
  }

  // Ambient towers further out
  for (let i = 0; i < 72; i++) {
    const h = 2 + Math.random() * 14;
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(0.6 + Math.random() * 1.2, h, 0.6 + Math.random() * 1.2),
      new THREE.MeshStandardMaterial({
        color: 0x062010,
        emissive: 0x0a3a18,
        emissiveIntensity: 0.08 + Math.random() * 0.14,
        roughness: 0.85,
        wireframe: Math.random() > 0.78,
      })
    );
    const a = Math.random() * Math.PI * 2;
    const r = 16 + Math.random() * 18;
    box.position.set(Math.cos(a) * r, h / 2, Math.sin(a) * r);
    root.add(box);
  }

  // Elevated highway ribbon
  const hwy = new THREE.Mesh(
    new THREE.BoxGeometry(28, 0.25, 1.4),
    new THREE.MeshStandardMaterial({
      color: 0x0a1810,
      emissive: 0x1a5030,
      emissiveIntensity: 0.35,
      metalness: 0.4,
      roughness: 0.4,
    })
  );
  hwy.position.set(6, 3.2, 4);
  hwy.rotation.y = -0.35;
  root.add(hwy);
}

function buildSectors(meta) {
  for (const [id, pos] of Object.entries(CITY_XY)) {
    const h = buildingHeight(id);
    const isOut = OUT.has(id);
    const geo = isOut
      ? new THREE.CylinderGeometry(0.85, 1.05, h, 6)
      : new THREE.BoxGeometry(1.6, h, 1.6);
    const mat = new THREE.MeshStandardMaterial({
      color: isOut ? 0x0a2030 : 0x0a2814,
      emissive: isOut ? 0x104050 : 0x145c28,
      emissiveIntensity: 0.25,
      roughness: 0.55,
      metalness: 0.2,
      wireframe: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    const w = toWorld(id);
    mesh.position.set(w.x, h / 2, w.z);
    mesh.userData = { locId: id, baseH: h, baseEmissive: mat.emissiveIntensity };
    mesh.castShadow = true;
    root.add(mesh);
    buildings.set(id, mesh);

    // neon rim
    const edge = new THREE.LineSegments(
      new THREE.EdgesGeometry(geo),
      new THREE.LineBasicMaterial({ color: isOut ? 0x80deea : 0x39ff14, transparent: true, opacity: 0.35 })
    );
    edge.position.copy(mesh.position);
    root.add(edge);

    const label = makeLabel((meta[id] && meta[id].name) || id.replace(/_/g, " "));
    label.position.set(w.x, h + 0.9, w.z);
    root.add(label);
    labelSprites.set(id, label);
  }

  // hardline edges
  const pts = [];
  for (const [a, b] of EDGES) {
    if (!CITY_XY[a] || !CITY_XY[b]) continue;
    const wa = toWorld(a);
    const wb = toWorld(b);
    const ha = buildingHeight(a);
    const hb = buildingHeight(b);
    pts.push(wa.x, Math.max(ha, 1) * 0.55, wa.z, wb.x, Math.max(hb, 1) * 0.55, wb.z);
  }
  const lineGeo = new THREE.BufferGeometry();
  lineGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  root.add(
    new THREE.LineSegments(
      lineGeo,
      new THREE.LineBasicMaterial({ color: 0x1f6b2e, transparent: true, opacity: 0.55 })
    )
  );
}

function addRainCode() {
  const n = 900;
  const positions = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 60;
    positions[i * 3 + 1] = Math.random() * 28;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 60;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const pts = new THREE.Points(
    geo,
    new THREE.PointsMaterial({
      color: 0x39ff14,
      size: 0.07,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    })
  );
  pts.name = "codeRain";
  root.add(pts);
}

export function initCity3D(canvas, opts = {}) {
  if (ready) return;
  onSelect = opts.onSelect || onSelect;
  onMove = opts.onMove || onMove;

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x010302, 0.2);
  renderer.shadowMap.enabled = true;

  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x010302, 0.028);

  camera = new THREE.PerspectiveCamera(48, 1, 0.1, 200);
  camera.position.set(18, 16, 22);

  controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.maxPolarAngle = Math.PI * 0.48;
  controls.minDistance = 8;
  controls.maxDistance = 55;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.35;
  controls.target.set(0, 2, 0);

  root = new THREE.Group();
  scene.add(root);

  scene.add(new THREE.AmbientLight(0x39ff14, 0.35));
  const key = new THREE.DirectionalLight(0x7cff7c, 1.1);
  key.position.set(12, 22, 8);
  key.castShadow = true;
  scene.add(key);
  const rim = new THREE.PointLight(0xff3b4e, 0.55, 40);
  rim.position.set(-10, 8, -8);
  scene.add(rim);

  addGridCity();
  buildSectors(opts.meta || {});
  addRainCode();

  agentsRoot = new THREE.Group();
  root.add(agentsRoot);

  const huntGeo = new THREE.BufferGeometry();
  huntLine = new THREE.Line(
    huntGeo,
    new THREE.LineBasicMaterial({ color: 0xff3b4e, linewidth: true, opacity: 0.85 })
  );
  root.add(huntLine);

  raycaster = new THREE.Raycaster();
  pointer = new THREE.Vector2();

  function resize() {
    const parent = canvas.parentElement;
    const w = parent.clientWidth || 640;
    const h = parent.clientHeight || 420;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener("resize", resize);

  canvas.addEventListener("pointerdown", () => {
    controls.autoRotate = false;
  });

  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects([...buildings.values()], false);
    if (hits[0]) {
      const id = hits[0].object.userData.locId;
      selectedId = id;
      onSelect(id);
    }
  });

  canvas.addEventListener("dblclick", (ev) => {
    const rect = canvas.getBoundingClientRect();
    pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects([...buildings.values()], false);
    if (hits[0]) onMove(hits[0].object.userData.locId);
  });

  const clock = new THREE.Clock();
  function tick() {
    animId = requestAnimationFrame(tick);
    const t = clock.getElapsedTime();
    controls.update();

    const rain = root.getObjectByName("codeRain");
    if (rain) {
      const arr = rain.geometry.attributes.position.array;
      for (let i = 0; i < arr.length; i += 3) {
        arr[i + 1] -= 0.12 + (i % 7) * 0.01;
        if (arr[i + 1] < 0) arr[i + 1] = 20 + Math.random() * 4;
      }
      rain.geometry.attributes.position.needsUpdate = true;
    }

    for (const [id, mesh] of buildings) {
      const pulse = id === selectedId ? 0.55 + Math.sin(t * 3) * 0.2 : mesh.userData.baseEmissive;
      mesh.material.emissiveIntensity = pulse;
      if (mesh.userData.neoHere) {
        mesh.scale.y = 1 + Math.sin(t * 2.2) * 0.04;
        mesh.position.y = (mesh.userData.baseH * mesh.scale.y) / 2;
      } else {
        mesh.scale.y = 1;
        mesh.position.y = mesh.userData.baseH / 2;
      }
    }

    renderer.render(scene, camera);
  }
  tick();
  ready = true;
}

export function setMapMode3D(on) {
  if (controls) controls.enabled = !!on;
  if (!on && animId) {
    /* keep rendering cheap when hidden — still ok */
  }
}

export function updateCity3D(data, meta = {}) {
  if (!ready) return;
  const neoLoc = data.location || "";
  const positions = data.agent_positions || {};
  const hunt = data.hunt_path || [];
  const heat = data.sector_heat || {};
  const styles = data.cast_style || {};
  const sel = selectedId || neoLoc;

  const sig = [neoLoc, sel, JSON.stringify(positions), hunt.join(">"), JSON.stringify(heat)].join("|");
  if (sig === lastSig) return;
  lastSig = sig;
  selectedId = sel;

  for (const [id, mesh] of buildings) {
    const hval = Number(heat[id] || 0);
    const here = id === neoLoc;
    const hunted = hunt.includes(id);
    const isSel = id === selectedId;
    mesh.userData.neoHere = here;
    if (OUT.has(id)) {
      mesh.material.emissive.setHex(0x104050);
      mesh.material.color.setHex(isSel ? 0x143848 : 0x0a2030);
    } else {
      mesh.material.emissive.setHex(hunted ? 0x5a1018 : here ? 0x1f8a34 : 0x145c28);
      mesh.material.color.setHex(isSel ? 0x123820 : here ? 0x0e3a1c : 0x0a2814);
    }
    mesh.userData.baseEmissive = hunted ? 0.55 : here ? 0.45 : 0.2 + Math.min(0.4, hval / 80);
    const lab = labelSprites.get(id);
    if (lab) lab.visible = isSel || here || hunted;
  }

  // agents
  while (agentsRoot.children.length) {
    const c = agentsRoot.children.pop();
    c.geometry?.dispose?.();
    c.material?.dispose?.();
  }
  const AGENTS = new Set(["smith", "jones", "brown"]);
  for (const [who, where] of Object.entries(positions)) {
    if (!CITY_XY[where]) continue;
    const w = toWorld(where);
    const h = buildingHeight(where);
    const st = styles[who] || {};
    let color = 0x39ff14;
    if (AGENTS.has(who)) color = 0xff3b4e;
    else if (st.faction === "system" || ["oracle", "architect", "keymaker", "merovingian"].includes(who))
      color = 0x80deea;
    if (who === "neo") color = 0xb4ffb4;
    const ball = new THREE.Mesh(
      new THREE.SphereGeometry(who === "neo" ? 0.38 : 0.28, 16, 16),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: who === "neo" ? 0.85 : 0.5,
        roughness: 0.35,
      })
    );
    const slot = (who.charCodeAt(0) % 5) * 0.35 - 0.7;
    ball.position.set(w.x + slot, h + 0.55, w.z + ((who.length % 3) - 1) * 0.25);
    agentsRoot.add(ball);
  }

  // hunt path
  if (hunt.length >= 2) {
    const pts = [];
    for (const id of hunt) {
      if (!CITY_XY[id]) continue;
      const w = toWorld(id);
      pts.push(new THREE.Vector3(w.x, buildingHeight(id) + 0.2, w.z));
    }
    huntLine.geometry.dispose();
    huntLine.geometry = new THREE.BufferGeometry().setFromPoints(pts);
    huntLine.visible = true;
  } else {
    huntLine.visible = false;
  }

  // ease camera toward Neo occasionally
  if (neoLoc && CITY_XY[neoLoc] && !controls._userTouched) {
    const w = toWorld(neoLoc);
    controls.target.lerp(new THREE.Vector3(w.x, 3, w.z), 0.04);
  }
}

export function resizeCity3D() {
  if (!ready || !renderer || !camera) return;
  const canvas = renderer.domElement;
  const parent = canvas.parentElement;
  const w = parent.clientWidth || 640;
  const h = parent.clientHeight || 420;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

export function isCity3DReady() {
  return ready;
}

/**
 * optimize-models.mjs — Compresse les modèles exportés par Blender et prépare les
 * données utilisées par le site.
 *
 *   .build/raw/*.glb        ->  models/*.glb            (meshopt + textures WebP ≤ 1024 px)
 *   .build/manifest/*.json  ->  js/data/manifest.js     (ancres, pivots, cotes : sert aux modèles de secours)
 *   .build/previews/*.png   ->  img/previews/*.webp     (images d'attente des visionneuses)
 *
 * Usage :  npm run optimize      (après `blender -b -P scripts/blender/build_all.py`)
 */
import { readFile, writeFile, readdir, mkdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, textureCompress, meshopt } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import sharp from 'sharp';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RAW = path.join(ROOT, '.build', 'raw');
const MAN = path.join(ROOT, '.build', 'manifest');
const PREV = path.join(ROOT, '.build', 'previews');
const OUT = path.join(ROOT, 'models');
const MAX_MODEL_BYTES = 3 * 1024 * 1024;     // objectif : < 3 Mo par modèle
const MAX_TOTAL_BYTES = 30 * 1024 * 1024;    // objectif : < 30 Mo au total

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });

await mkdir(OUT, { recursive: true });
await mkdir(path.join(ROOT, 'img', 'previews'), { recursive: true });
await mkdir(path.join(ROOT, 'js', 'data'), { recursive: true });

const files = (await readdir(RAW)).filter((f) => f.endsWith('.glb')).sort();
let total = 0;
const report = [];
for (const file of files) {
  const doc = await io.read(path.join(RAW, file));
  await doc.transform(
    dedup(),
    // keepLeaves : on GARDE les empties (ancres) même s'ils n'ont ni maillage ni enfant
    prune({ keepLeaves: true, keepExtras: true }),
    textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024], quality: 85 }),
    meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  );
  const outPath = path.join(OUT, file);
  await io.write(outPath, doc);
  const { size } = await stat(outPath);
  const rawSize = (await stat(path.join(RAW, file))).size;
  total += size;
  const anchors = doc.getRoot().listNodes().filter((n) => n.getName().startsWith('anchor_')).length;
  report.push({ file, raw: rawSize, out: size, anchors });
  if (size > MAX_MODEL_BYTES) console.warn(`⚠ ${file} dépasse 3 Mo (${(size / 1048576).toFixed(2)} Mo)`);
}

// manifeste JS (importé par js/core/fallbacks.js)
const manifest = {};
for (const f of (await readdir(MAN)).filter((f) => f.endsWith('.json')).sort()) {
  const m = JSON.parse(await readFile(path.join(MAN, f), 'utf8'));
  manifest[m.model] = {
    bboxMin: m.bbox_min, bboxMax: m.bbox_max, anchors: m.anchors, keep: m.keep,
    triangles: m.triangles, info: m.info,
  };
}
const js = `/**
 * manifest.js — GÉNÉRÉ AUTOMATIQUEMENT par scripts/optimize-models.mjs (ne pas éditer).
 * Pour chaque modèle : boîte englobante, ancres et pivots des pièces animables,
 * en centimètres dans l'espace du site (X = avant, Y = haut, Z = vers la vitre).
 */
export const MANIFEST = ${JSON.stringify(manifest, null, 1)};
`;
await writeFile(path.join(ROOT, 'js', 'data', 'manifest.js'), js);

// aperçus -> WebP (posters des visionneuses)
if (existsSync(PREV)) {
  for (const f of (await readdir(PREV)).filter((f) => f.endsWith('.png') && !/_alt|_zoom|noglass/.test(f))) {
    await sharp(path.join(PREV, f)).resize({ width: 900, withoutEnlargement: true })
      .webp({ quality: 82, alphaQuality: 90 })
      .toFile(path.join(ROOT, 'img', 'previews', f.replace('.png', '.webp')));
  }
}

console.table(report.map((r) => ({
  modèle: r.file, 'brut (Ko)': Math.round(r.raw / 1024), 'compressé (Ko)': Math.round(r.out / 1024), ancres: r.anchors,
})));
console.log(`Total : ${(total / 1048576).toFixed(2)} Mo ${total > MAX_TOTAL_BYTES ? '⚠ au-delà de 30 Mo' : '(objectif < 30 Mo respecté)'}`);

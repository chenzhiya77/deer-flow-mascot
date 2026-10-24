// Reference numbers straight from the opening, for `python opening_preview.py --check dump.json`:
// duckPose / seatWorld / bodyFrame().pitch / horseX every 1/240 s over story 0-7.6 s, and the camera
// (story time, camX / camY / camZ, hand-held drift) at every 60 fps frame of the opening.
//   OPENING_SRC=<harness-rag-opening>/src npx tsx opening_dump.mts > dump.json
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const src = process.env.OPENING_SRC;
if (!src) {
  console.error("set OPENING_SRC to the opening's src folder");
  process.exit(1);
}
const load = (p: string) => import(pathToFileURL(path.resolve(src, p)).href);
const {duckPose, seatWorld} = await load('characters/duckMotion.ts');
const {bodyFrame} = await load('characters/horseRig.ts');
const {camX, camY, camZ, realToStory, horseX, FPS, DURATION_FRAMES} = await load('lib/timeline.ts');
const {fbm1} = await load('lib/math.ts');

const poses = [];
for (let i = 0; i <= 7.6 * 240; i++) {
  const T = i / 240;
  const s = seatWorld(T);
  poses.push({T, ...duckPose(T), seatX: s.x, seatY: s.y, pitch: bodyFrame(T).pitch, horseX: horseX(T)});
}
const cams = [];
for (let f = 0; f < DURATION_FRAMES; f++) {
  const t = f / FPS;
  const T = realToStory(t);
  cams.push({f, t, T, x: camX(T), y: camY(T), z: camZ(T, t), hx: fbm1(T * 0.35, 1) * 7, hy: fbm1(T * 0.3, 2) * 4.5});
}
process.stdout.write(JSON.stringify({poses, cams}));

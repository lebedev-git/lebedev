// Запуск next из другого проекта с правильным cwd: относительные пути
// (DB_PATH=data/eng.db, .env.local) считаются от каталога проекта.
//   node tools/run_next.mjs <каталог-проекта> dev -p 3100
import { createRequire } from "node:module";
import { resolve } from "node:path";

const dir = resolve(process.argv[2]);
process.chdir(dir);
process.argv.splice(2, 1);
createRequire(import.meta.url)(resolve(dir, "node_modules/next/dist/bin/next"));

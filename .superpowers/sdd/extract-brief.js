const fs = require('fs')
const planPath = process.argv[2]
const n = Number(process.argv[3])
const outPath = process.argv[4]
const plan = fs.readFileSync(planPath, 'utf8')
const lines = plan.split(/\n/)
let out = []
let intask = false
let fence = false
const taskRe = /^#+[ \t]+Task[ \t]+\d+/
const thisRe = new RegExp(`^#+[ \\t]+Task[ \\t]+${n}([^0-9]|$)`)
for (const line of lines) {
  if (line.startsWith('```')) fence = !fence
  if (!fence && taskRe.test(line)) intask = thisRe.test(line)
  if (intask) out.push(line)
}
if (!out.length) {
  console.error(`task ${n} not found`)
  process.exit(3)
}
fs.writeFileSync(outPath, out.join('\n') + '\n')
console.log(`wrote ${outPath}: ${out.length} lines`)

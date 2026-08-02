import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'

const slidesRoot = path.resolve('slides')
const conversationPattern = /^speaker\s*([12])\s*[:：]\s*(.+)$/i
let courseCount = 0
let slideCount = 0
let segmentCount = 0
const errors = []

async function walk(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const markdowns = entries.filter((entry) => entry.isFile() && /^\d+\.md$/.test(entry.name))
  if (markdowns.length) courseCount += 1

  for (const markdown of markdowns) {
    slideCount += 1
    const base = markdown.name.replace(/\.md$/, '')
    const conversations = entries.filter((entry) => entry.isFile() && entry.name.startsWith(`${base}.conversation`))
    if (!conversations.length) errors.push(`${path.join(directory, markdown.name)} 缺少对话文件`)
    for (const conversation of conversations) {
      const content = await readFile(path.join(directory, conversation.name), 'utf8')
      const segments = content.split(/\r?\n/).filter((line) => conversationPattern.test(line.trim()))
      if (!segments.length) errors.push(`${path.join(directory, conversation.name)} 没有有效 Speaker 1/2 对话`)
      segmentCount += segments.length
    }
  }

  await Promise.all(entries.filter((entry) => entry.isDirectory()).map((entry) => walk(path.join(directory, entry.name))))
}

await walk(slidesRoot)
if (!courseCount || !slideCount) errors.push('slides 中没有找到课程素材')
if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}
console.log(`内容检查通过：${courseCount} 门课程，${slideCount} 个章节，${segmentCount} 条对话。`)

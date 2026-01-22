const pptxgen = require('pptxgenjs');
const html2pptx = require('/Users/hehe/pycharm_projects/aigc/backend/.claude/skills/pptx/scripts/html2pptx.js');
const path = require('path');

async function createPresentation() {
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'AIGC Team';
  pptx.title = 'Tool Calls 显示流程分析';
  pptx.subject = '技术流程分析文档';

  const slidesDir = path.join(__dirname, 'slides');

  // Slide 1: 封面
  await html2pptx(path.join(slidesDir, 'slide01-cover.html'), pptx);

  // Slide 2: 数据流概览
  await html2pptx(path.join(slidesDir, 'slide02-overview.html'), pptx);

  // Slide 3: 数据获取流程
  await html2pptx(path.join(slidesDir, 'slide03-data-fetch.html'), pptx);

  // Slide 4: 工具调用提取流程
  await html2pptx(path.join(slidesDir, 'slide04-extraction.html'), pptx);

  // Slide 5: 用户交互流程
  await html2pptx(path.join(slidesDir, 'slide05-interaction.html'), pptx);

  // Slide 6: 问题诊断
  await html2pptx(path.join(slidesDir, 'slide06-diagnosis.html'), pptx);

  // Slide 7: 调试检查清单
  await html2pptx(path.join(slidesDir, 'slide07-checklist.html'), pptx);

  // Slide 8: 总结与下一步
  await html2pptx(path.join(slidesDir, 'slide08-summary.html'), pptx);

  // Save
  const outputPath = path.join(__dirname, 'Tool_Calls_Flow_Analysis.pptx');
  await pptx.writeFile({ fileName: outputPath });
}

createPresentation().catch(error => {
  process.exit(1);
});

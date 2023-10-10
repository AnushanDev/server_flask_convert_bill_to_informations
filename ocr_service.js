import { createWorker } from 'tesseract.js';

const worker = createWorker({
  logger: m => console.log(m),
});

async function recognizeImage() {
  await worker.load();
  await worker.loadLanguage('eng');
  await worker.initialize('eng');
  const { data: { text } } = await worker.recognize('path_to_image.png');
  console.log(text);
  await worker.terminate();
}

recognizeImage();

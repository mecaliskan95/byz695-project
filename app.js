process.noDeprecation = true;

const { ocr } = require('llama-ocr');
const path = require('path');

const runOCR = async (imagePath) => {
  const apiKey = 'key';

  try {
    const markdown = await ocr({
      filePath: imagePath,
      apiKey: apiKey,
      language: 'tur'
    });
    console.log(markdown);
    return markdown;
  } catch (error) {
    console.error('Error during OCR processing:', error);
    process.exit(1);
  }
};

const imagePath = process.argv[2];
if (imagePath) {
  runOCR(imagePath).then(markdown => {
    if (markdown) {
      process.exit(0);
    } else {
      process.exit(1);
    }
  });
} else {
  console.error('No image path provided');
  process.exit(1);
}
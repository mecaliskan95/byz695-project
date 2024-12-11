process.noDeprecation = true;

const { ocr } = require('llama-ocr');
const path = require('path');

const runOCR = async (imagePath) => {
  const apiKey = '642af0a977577412500f7aeb424b007353d921f3aae4466e8f38af48e158df56';

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
      console.log(markdown);
      process.exit(0);
    } else {
      process.exit(1);
    }
  });
} else {
  console.error('No image path provided');
  process.exit(1);
}
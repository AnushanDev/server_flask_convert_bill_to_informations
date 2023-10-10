const T = require("tesseract.js");

const imagePath = process.argv[2];
if (!imagePath) {
    console.error("Please provide an image path.");
    process.exit(1);
}

T.recognize(imagePath, 'eng')
    .then(out => {
        console.log(out.data.text);
    })
    .catch(error => {
        console.error("Error processing the image:", error);
    });


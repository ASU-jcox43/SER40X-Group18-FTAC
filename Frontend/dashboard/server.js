const express = require("express");
const multer = require("multer");
const fs = require("fs");
const path = require("path");

const app = express();
const PORT = 3000;

// Ensure uploads folder exists 
if (!fs.existsSync("uploads")) {
  fs.mkdirSync("uploads")
}

// Multer storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/");
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);
  }
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === "application/pdf") {
      cb(null, true);
    } else {
      cb(new Error("Only PDFs allowed"));
    }
  }
});

// serve static files
app.use(express.static("."));           // serve frontend
app.use("/uploads", express.static("uploads")); // allow access to uploaded PDFs

// upload route
app.post("/upload", upload.single("pdfFile"), (req, res) => {
  res.status(200).send("Upload successful");
});

// get upload files
app.get("/files", (req, res) => {
  fs.readdir("uploads", (err, files) => {
    if (err) return res.json([]);
    res.json(files);
  });
});

// start server
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
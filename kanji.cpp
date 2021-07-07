#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>
#include <tesseract/publictypes.h>
int main(int argc, char *argv[]){
    tesseract::TessBaseAPI *api = new tesseract::TessBaseAPI();
// Initialize tesseract-ocr with Japanese, without specifying tessdata path
    if (api->Init(NULL, "jpn")) {
        fprintf(stderr, "Could not initialize tesseract.\n");
        exit(1);
    }
// Open input image with leptonica library
  Pix *image = pixRead(argv[1]);
  api->SetImage(image);
  api->SetVariable("save_blob_choices", "T");
  api->SetVariable("tessedit_char_blacklist", "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ");
  api->SetPageSegMode(tesseract::PSM_SINGLE_CHAR);
  api->Recognize(NULL);

  tesseract::ResultIterator* ri = api->GetIterator();
  tesseract::PageIteratorLevel level = tesseract::RIL_SYMBOL;
  if(ri != 0) {
      do {
          const char* symbol = ri->GetUTF8Text(level);
          float conf = ri->Confidence(level);
          if(symbol != 0) {
              tesseract::ChoiceIterator ci(*ri);
              do {
                  const char* choice = ci.GetUTF8Text();
                  printf("%s (%.2f%%)\n", choice, ci.Confidence());
              } while(ci.Next());
          }
          delete[] symbol;
      } while((ri->Next(level)));
  }
// Destroy used object and release memory
    api->End();
    pixDestroy(&image);
    return 0;
}


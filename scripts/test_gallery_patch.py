from pathlib import Path
import sys
s=(Path(sys.argv[1])/'smali_classes46/com/nasa/edateor/exsam/A11/EnterOneActivity.smali').read_text()
for x in ['GalleryImages;->attach(Landroid/app/Activity;)V','GalleryImages;->apply(Landroid/app/Activity;)V','GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V','method protected onActivityResult(IILandroid/content/Intent;)V']: assert x in s,x
print('Gallery patch static checks passed')

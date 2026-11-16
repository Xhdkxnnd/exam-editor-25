#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]); p=root/'smali_classes46/com/nasa/edateor/exsam/A11/EnterOneActivity.smali'; s=p.read_text()
needle='    invoke-direct {p0}, Lcom/nasa/edateor/exsam/A11/EnterOneActivity;->initializeLogic()V\n'
if 'GalleryImages;->attach' not in s:
 assert needle in s; s=s.replace(needle,needle+'    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->attach(Landroid/app/Activity;)V\n',1)
needle='    :goto_0\n    iget-object v0, p0, Lcom/nasa/edateor/exsam/A11/EnterOneActivity;->saveX:Landroid/content/SharedPreferences;\n'
if 'GalleryImages;->apply' not in s:
 assert needle in s; s=s.replace(needle,'    :goto_0\n    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->apply(Landroid/app/Activity;)V\n'+needle.split('\n',1)[1]+'\n',1)
if 'method protected onActivityResult(IILandroid/content/Intent;)V' not in s:
 s+='\n.method protected onActivityResult(IILandroid/content/Intent;)V\n    .locals 0\n    invoke-super {p0, p1, p2, p3}, Landroidx/appcompat/app/AppCompatActivity;->onActivityResult(IILandroid/content/Intent;)V\n    invoke-static {p0, p1, p2, p3}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V\n    return-void\n.end method\n'
p.write_text(s); print('Patched',p)

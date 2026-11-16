#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'smali_classes46/com/nasa/edateor/exsam/A11/EnterOneActivity.smali'
s=p.read_text()
needle='    invoke-direct {p0}, Lcom/nasa/edateor/exsam/A11/EnterOneActivity;->initializeLogic()V\\n'
if 'GalleryImages;->attach' not in s:
    assert needle in s, 'onCreate insertion point missing'
    s=s.replace(needle, needle+'    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->attach(Landroid/app/Activity;)V\\n', 1)
start=s.index('.method public _saveT()V')
end=s.index('.end method', start)
method=s[start:end]
apply='    invoke-static {p0}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->apply(Landroid/app/Activity;)V\\n'
if 'GalleryImages;->apply' not in method:
    needle='    :goto_0\\n    iget-object v0, p0, Lcom/nasa/edateor/exsam/A11/EnterOneActivity;->saveX:Landroid/content/SharedPreferences;\\n'
    assert needle in method, '_saveT save point missing'
    method=method.replace(needle, '    :goto_0\\n'+apply+'    iget-object v0, p0, Lcom/nasa/edateor/exsam/A11/EnterOneActivity;->saveX:Landroid/content/SharedPreferences;\\n', 1)
    s=s[:start]+method+s[end:]
if 'method protected onActivityResult(IILandroid/content/Intent;)V' not in s:
    s+='\\n.method protected onActivityResult(IILandroid/content/Intent;)V\\n    .locals 0\\n    invoke-super {p0, p1, p2, p3}, Landroidx/appcompat/app/AppCompatActivity;->onActivityResult(IILandroid/content/Intent;)V\\n    invoke-static {p0, p1, p2, p3}, Lcom/nasa/edateor/exsam/A11/GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V\\n    return-void\\n.end method\\n'
p.write_text(s)
print('Patched', p)

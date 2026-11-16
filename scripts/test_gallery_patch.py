from pathlib import Path
import sys
root=Path(sys.argv[1])
smali=list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/EnterOneActivity.smali"))
assert len(smali)==1
s=smali[0].read_text()
for x in ['GalleryImages;->attach(Landroid/app/Activity;)V','GalleryImages;->apply(Landroid/app/Activity;)V','GalleryImages;->onActivityResult(Landroid/app/Activity;IILandroid/content/Intent;)V']: assert x in s,x
start=s.index('.method public _saveT()V'); end=s.index('.end method',start)
assert 'GalleryImages;->apply' in s[start:end], 'apply call must be inside _saveT'
adapters=list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$Listview1Adapter.smali"))
assert len(adapters)==1
a=adapters[0].read_text()
start=a.index('.method public getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;'); end=a.index('.end method',start)
assert 'GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V' in a[start:end]
print('Gallery save and question-template rendering checks passed')

adapters5=list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity$Listview1_5Adapter.smali"))
assert len(adapters5)==1
a5=adapters5[0].read_text()
start=a5.index('.method public getView(ILandroid/view/View;Landroid/view/ViewGroup;)Landroid/view/View;'); end=a5.index('.end method',start)
assert 'GalleryImages;->renderQuestion(Landroid/app/Activity;Landroid/view/View;Ljava/util/HashMap;)V' in a5[start:end]

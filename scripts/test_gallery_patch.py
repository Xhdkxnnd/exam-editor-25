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

# Verify the primary PDF page uses raster drawing so emoji and embedded images
# survive PDF export and printing. The continuation page remains intentionally untouched.
activities=list(root.glob("smali_classes*/com/nasa/edateor/exsam/A11/ExzamVActivity.smali"))
assert len(activities)==1
v=activities[0].read_text()
start=v.index("PD(Landroid/graphics/pdf/PdfDocument;)V")
start=v.rfind(".method",0,start)
end=v.index(".end method",start)
assert "GalleryImages;->drawPdfRaster(Landroid/view/View;Landroid/graphics/Canvas;)V" in v[start:end], "primary PDF page must use raster drawing"
print('Gallery save, question-template rendering, and primary PDF raster checks passed')

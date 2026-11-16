package com.nasa.edateor.exsam.A11;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.net.Uri;
import android.view.View;
import android.view.ViewGroup;
import android.widget.*;
import java.io.*;
import java.lang.reflect.Field;
import java.util.*;

public final class GalleryImages {
 private static final int REQUEST=27125;
 private static final String PREF="exam25_gallery_pending";
 private static final Map<Activity,State> STATES=new WeakHashMap<>();
 private static class State { LinearLayout strip; ArrayList<String> paths; State(LinearLayout s,ArrayList<String> p){strip=s;paths=p;} }
 private static Object field(Object o,String n)throws Exception { Field f=o.getClass().getDeclaredField(n); f.setAccessible(true); return f.get(o); }
 private static String key(Activity a)throws Exception { return field(a,"ID")+"_"+field(a,"pppp")+"_"+field(a,"Tipee")+"_"+(int)(double)(Double)field(a,"Position"); }
 @SuppressWarnings("unchecked") private static ArrayList<String> paths(Activity a) {
  ArrayList<String> out=new ArrayList<>(); try {
   SharedPreferences p=a.getSharedPreferences(PREF,0); String k=key(a), raw=p.getString(k,"");
   if(p.contains(k)){ if(!raw.isEmpty()) out.addAll(Arrays.asList(raw.split("\\n"))); return out; }
   if(!"A".equals(field(a,"Tipee"))){ ArrayList<HashMap<String,Object>> list=(ArrayList<HashMap<String,Object>>)field(a,"list_allQ"); Object old=list.get((int)(double)(Double)field(a,"Position")).get("images"); if(old instanceof List) for(Object x:(List<?>)old) if(x!=null)out.add(x.toString()); }
  }catch(Exception ignored){} return out;
 }
 private static void save(Activity a,ArrayList<String> paths){try{StringBuilder b=new StringBuilder();for(String p:paths){if(b.length()>0)b.append('\n');b.append(p);}a.getSharedPreferences(PREF,0).edit().putString(key(a),b.toString()).apply();}catch(Exception ignored){}}
 public static void attach(final Activity a){
  try {
   LinearLayout parent=(LinearLayout)field(a,"linear1"); ArrayList<String> selected=paths(a);
   LinearLayout block=new LinearLayout(a);block.setOrientation(1);
   Button pick=new Button(a);pick.setText("إضافة صور من المعرض");
   pick.setOnClickListener(v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("image/*");i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);a.startActivityForResult(i,REQUEST);});
   block.addView(pick);HorizontalScrollView scroll=new HorizontalScrollView(a);LinearLayout strip=new LinearLayout(a);strip.setOrientation(0);scroll.addView(strip);block.addView(scroll);
   parent.addView(block,Math.max(0,parent.getChildCount()-1));STATES.put(a,new State(strip,selected));render(a,strip,selected);
  }catch(Exception e){Toast.makeText(a,"تعذر تهيئة معرض الصور",Toast.LENGTH_LONG).show();}
 }
 private static int dp(Activity a,int n){return (int)(n*a.getResources().getDisplayMetrics().density+.5f);}
 private static Bitmap bitmap(Activity a,String path){BitmapFactory.Options o=new BitmapFactory.Options();o.inSampleSize=4;return BitmapFactory.decodeFile(new File(a.getFilesDir(),path).getAbsolutePath(),o);}
 private static void render(Activity a,LinearLayout strip,ArrayList<String> list){
  strip.removeAllViews();for(int n=0;n<list.size();n++){final String path=list.get(n);final int index=n;LinearLayout item=new LinearLayout(a);item.setOrientation(1);ImageView image=new ImageView(a);image.setScaleType(ImageView.ScaleType.CENTER_CROP);Bitmap b=bitmap(a,path);if(b!=null)image.setImageBitmap(b);item.addView(image,new LinearLayout.LayoutParams(dp(a,88),dp(a,88)));Button del=new Button(a);del.setText("حذف");del.setOnClickListener(v->{list.remove(index);new File(a.getFilesDir(),path).delete();save(a,list);render(a,strip,list);});item.addView(del);strip.addView(item);}
 }
 public static void onActivityResult(Activity a,int request,int result,Intent data){
  if(request!=REQUEST||result!=Activity.RESULT_OK||data==null)return;
  try{State s=STATES.get(a);if(s==null)return; if(data.getClipData()!=null){for(int n=0;n<data.getClipData().getItemCount();n++)copy(a,data.getClipData().getItemAt(n).getUri(),s.paths);}else if(data.getData()!=null)copy(a,data.getData(),s.paths);save(a,s.paths);render(a,s.strip,s.paths);}catch(Exception e){Toast.makeText(a,"تعذر استيراد الصور",Toast.LENGTH_LONG).show();}
 }
 private static void copy(Activity a,Uri uri,ArrayList<String> list)throws Exception{
  File dir=new File(a.getFilesDir(),"question_images");if(!dir.exists()&&!dir.mkdirs())throw new IOException("mkdir");String rel="question_images/"+UUID.randomUUID()+".img";InputStream in=a.getContentResolver().openInputStream(uri);if(in==null)throw new IOException("open");FileOutputStream out=new FileOutputStream(new File(a.getFilesDir(),rel));byte[] buf=new byte[8192];try{int n;while((n=in.read(buf))>0)out.write(buf,0,n);}finally{in.close();out.close();}list.add(rel);
 }
 @SuppressWarnings("unchecked") public static void apply(Activity a){
  try{ArrayList<String> selected=paths(a);if("A".equals(field(a,"Tipee"))){((HashMap<String,Object>)field(a,"mmmo")).put("images",new ArrayList<>(selected));}else{ArrayList<HashMap<String,Object>> list=(ArrayList<HashMap<String,Object>>)field(a,"list_allQ");list.get((int)(double)(Double)field(a,"Position")).put("images",new ArrayList<>(selected));}a.getSharedPreferences(PREF,0).edit().remove(key(a)).apply();}catch(Exception e){Toast.makeText(a,"تعذر حفظ الصور",Toast.LENGTH_LONG).show();}
 }
 /** Adds saved question images to the actual question row used by the template and PDF. */
 @SuppressWarnings("unchecked") public static void renderQuestion(Activity a,View row,HashMap<String,Object> question){
  if(!(row instanceof LinearLayout)||question==null)return;
  LinearLayout root=(LinearLayout)row;
  while(root.getChildCount()>1)root.removeViewAt(1);
  Object value=question.get("images");
  if(!(value instanceof List))return;
  List<?> paths=(List<?>)value;if(paths.isEmpty())return;
  LinearLayout strip=new LinearLayout(a);strip.setOrientation(LinearLayout.HORIZONTAL);
  for(Object item:paths){
   if(item==null)continue;
   File file=new File(a.getFilesDir(),item.toString());if(!file.isFile())continue;
   Bitmap b=bitmap(a,item.toString());if(b==null)continue;
   ImageView image=new ImageView(a);image.setScaleType(ImageView.ScaleType.CENTER_INSIDE);image.setImageBitmap(b);
   // Zero margins make neighboring images touch without side gaps.
   LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(a,150),dp(a,120));
   lp.setMargins(0,0,0,0);
   strip.addView(image,lp);
  }
  if(strip.getChildCount()>0){
   HorizontalScrollView scroll=new HorizontalScrollView(a);
   scroll.setFillViewport(false);
   scroll.setHorizontalScrollBarEnabled(false);
   scroll.addView(strip,new HorizontalScrollView.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT,dp(a,120)));
   root.addView(scroll,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,dp(a,120)));
   // A small blank area below the image row gives the student room to answer.
   View answerSpace=new View(a);
   root.addView(answerSpace,new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,dp(a,28)));
  }

 }
 /** Rasterizes the PDF page so fallback emoji glyphs are embedded as pixels, not printer-dependent fonts. */
 public static void drawPdfRaster(View view, Canvas target) {
  if(view==null||target==null)return;
  int width=view.getWidth(), height=view.getHeight();
  if(width<=0||height<=0){view.draw(target);return;}
  Bitmap page=null;
  try {
   page=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888);
   Canvas raster=new Canvas(page);
   view.draw(raster);
   target.drawBitmap(page,0f,0f,null);
  } catch(Throwable failure) {
   view.draw(target);
  } finally {
   if(page!=null&&!page.isRecycled())page.recycle();
  }
 }
}

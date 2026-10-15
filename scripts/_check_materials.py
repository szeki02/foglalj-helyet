# -*- coding: utf-8 -*-
# verify layer materials + capture Rendered-mode views to rhino\materials_*.png
import Rhino
import scriptcontext as sc
import System

doc = sc.doc
ok = 0
bad = []
for L in doc.Layers:
    if L.IsDeleted:
        continue
    rm = L.RenderMaterial
    if rm is not None and (rm.Name or '').startswith('AU6 '):
        ok += 1
    elif L.FullPath.startswith(('01_', '02_', '03_', '04_', 'ADDITIONS::Pavilion::')):
        bad.append(L.FullPath)
print('layers with AU6 material: %d' % ok)
print('model layers without: ' + '; '.join(bad))

mode = Rhino.Display.DisplayModeDescription.FindByName('Rendered')
view = doc.Views.ActiveView
old_mode = view.ActiveViewport.DisplayMode
for vname, fn in (('Pavilion_overview', 'materials_pavilion.png'),
                  ('Courtyard_north_end', 'materials_north.png'),
                  ('Pallet_planters_photo37', 'materials_planters.png')):
    i = doc.NamedViews.FindByName(vname)
    if i < 0:
        print('no view ' + vname)
        continue
    doc.NamedViews.Restore(i, view.ActiveViewport)
    view.ActiveViewport.DisplayMode = mode
    view.Redraw()
    bmp = view.CaptureToBitmap(System.Drawing.Size(1600, 1000))
    p = r'C:\Users\David\DEV\Alfoldi_utca_6\rhino\\' + fn
    bmp.Save(p, System.Drawing.Imaging.ImageFormat.Png)
    print('saved ' + p)
view.ActiveViewport.DisplayMode = old_mode
view.Redraw()

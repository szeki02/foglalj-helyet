# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - capture review images through the main perspective view without disturbing it.
# Usage (inside Rhino):  execfile(this); capture(SHOTS)  - SHOTS = [(file, layer_state, mode, cam_snz, target_snz, lens)]
# Positions are (s, n, z) in the yard frame. During the capture, vegetation, street labels, marker boxes and other
# clutter are hidden; the view's camera, display mode and all layer visibility are restored afterwards.
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System
from Rhino.DocObjects.Tables import RestoreLayerProperties

doc = sc.doc
OUT = 'C:/Users/David/DEV/Alfoldi_utca_6/rhino/'
C_WORLD = rg.Point3d(-10.31, -19.80, 0)
U = rg.Vector3d(-0.33761, 0.94128, 0)
V = rg.Vector3d(0.94130, 0.33757, 0)
L = 16 * 1.157
PL = rg.Plane(C_WORLD, U, -V)
HIDE = ('03_Vegetation::Tree_Crowns', '03_Vegetation::Tree_Trunks_Branches', '07_OSM_Context::Street_Labels',
        '07_OSM_Context::Trees', '06_Reference', '09_Workshops::_zones', 'D5_cameras', 'D5_proxy::Street_Trees')
HIDE_OBJECTS_ON = ('ADDITIONS',)     # markup boxes sit directly on this layer; its sub-layers (pavilion) stay visible


def P(snz):
    s, n, z = snz
    return PL.PointAt(L - s, n, z)


def capture(shots, view_name='Pallet_planters_photo37', size=(1400, 900)):
    view = [v for v in doc.Views if v.ActiveViewport.Name == view_name][0]
    vp = view.ActiveViewport
    keep_vi = Rhino.DocObjects.ViewportInfo(vp)
    keep_mode = vp.DisplayMode
    modes = dict((m.EnglishName, m) for m in Rhino.Display.DisplayModeDescription.GetDisplayModes())
    S = doc.NamedLayerStates
    S.Save('_au6_cap_tmp')
    current = doc.Layers.CurrentLayerIndex
    doc.Layers.SetCurrentLayerIndex(doc.Layers.FindByFullPath('Default', -1), True)   # current layer can't be hidden
    hidden = [o.Id for o in doc.Objects
              if doc.Layers[o.Attributes.LayerIndex].FullPath in HIDE_OBJECTS_ON and o.Visible]
    for i in hidden:
        doc.Objects.Hide(i, True)
    done = []
    try:
        vp.ChangeToPerspectiveProjection(True, 24)
        for shot in shots:
            fn, state, mode, cam, tgt, lens = shot[:6]
            extra = tuple(shot[6]) if len(shot) > 6 else ()     # optional: more layer prefixes to hide (e.g. a roof)
            S.Restore(state, RestoreLayerProperties.Visible)
            for L_ in doc.Layers:
                if L_.FullPath.startswith(HIDE + extra) and L_.IsVisible:
                    L_.IsVisible = False
                    doc.Layers.Modify(L_, L_.Index, True)
            vp.DisplayMode = modes[mode]
            vp.Camera35mmLensLength = lens
            vp.SetCameraLocations(P(tgt), P(cam))
            view.Redraw()
            view.CaptureToBitmap(System.Drawing.Size(size[0], size[1])).Save(OUT + fn)
            done.append(fn)
    finally:
        for i in hidden:
            doc.Objects.Show(i, True)
        S.Restore('_au6_cap_tmp', RestoreLayerProperties.All)
        S.Delete('_au6_cap_tmp')
        doc.Layers.SetCurrentLayerIndex(current, True)
        vp.SetViewProjection(keep_vi, True)
        vp.DisplayMode = keep_mode
        view.Redraw()
    return done

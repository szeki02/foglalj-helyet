# -*- coding: utf-8 -*-
# IronPython 2.7 / Rhino 7 - render materials for the Alfoldi utca 6 courtyard model, assigned BY LAYER.
# Re-runnable: materials are named 'AU6 ...'; on re-run the old 'AU6 ...' render materials are replaced.
# Every object uses MaterialSource = MaterialFromLayer, so objects created later by the build scripts on these
# layers pick the material up automatically. Diffuse colours follow the photo-derived layer colours.
import Rhino
import scriptcontext as sc
from System.Drawing import Color
from Rhino.Render import RenderMaterial

doc = sc.doc

# name: (diffuse rgb, reflectivity, glossiness 0..1, transparency, ior, metallic)
MATS = {
    # --- metals
    'AU6 Steel painted blue-grey':  ((70, 105, 125), 0.12, 0.55, 0, 1.0, False),
    'AU6 Steel painted dark':       ((48, 50, 52), 0.10, 0.50, 0, 1.0, False),
    'AU6 Steel painted orange':     ((215, 120, 40), 0.10, 0.55, 0, 1.0, False),
    'AU6 Steel painted green':      ((40, 110, 85), 0.12, 0.60, 0, 1.0, False),
    'AU6 Aluminium satin':          ((170, 172, 170), 0.45, 0.60, 0, 1.0, True),
    'AU6 Galvanised steel':         ((178, 182, 184), 0.40, 0.45, 0, 1.0, True),
    'AU6 Zinc / profiled sheet':    ((182, 188, 192), 0.35, 0.50, 0, 1.0, True),
    'AU6 Corrugated sheet rusty':   ((120, 92, 70), 0.08, 0.25, 0, 1.0, False),
    'AU6 Steel mesh':               ((150, 155, 160), 0.30, 0.40, 0.55, 1.0, True),
    'AU6 Downpipe painted':         ((190, 120, 70), 0.10, 0.50, 0, 1.0, False),
    'AU6 Rail steel':               ((90, 90, 95), 0.35, 0.50, 0, 1.0, True),
    # --- glass / plastics
    'AU6 Glass clear':              ((150, 185, 200), 0.12, 0.98, 0.85, 1.52, False),
    'AU6 Glass dark facade':        ((60, 72, 82), 0.25, 0.95, 0.45, 1.52, False),
    'AU6 Polycarbonate translucent': ((205, 212, 216), 0.12, 0.85, 0.60, 1.58, False),
    'AU6 Plastic black':            ((28, 28, 28), 0.08, 0.60, 0, 1.0, False),
    'AU6 Plastic green':            ((40, 110, 50), 0.08, 0.60, 0, 1.0, False),
    'AU6 Fabric black':             ((35, 35, 35), 0.00, 0.00, 0, 1.0, False),
    'AU6 Roof membrane grey':       ((105, 105, 105), 0.03, 0.20, 0, 1.0, False),
    # --- masonry / render / concrete
    'AU6 Render grey west':         ((128, 128, 126), 0.00, 0.00, 0, 1.0, False),
    'AU6 Render beige east':        ((214, 196, 140), 0.00, 0.00, 0, 1.0, False),
    'AU6 Render beige exposed':     ((205, 190, 150), 0.00, 0.00, 0, 1.0, False),
    'AU6 Render dark grey':         ((75, 75, 75), 0.00, 0.00, 0, 1.0, False),
    'AU6 Render street wall':       ((150, 150, 145), 0.00, 0.00, 0, 1.0, False),
    'AU6 Paint white patch':        ((240, 240, 236), 0.02, 0.15, 0, 1.0, False),
    'AU6 Brick yellow north':       ((196, 170, 125), 0.00, 0.00, 0, 1.0, False),
    'AU6 Brick exposed':            ((170, 120, 85), 0.00, 0.00, 0, 1.0, False),
    'AU6 Brick red':                ((165, 75, 55), 0.00, 0.00, 0, 1.0, False),
    'AU6 Brick fire pit':           ((185, 85, 55), 0.00, 0.00, 0, 1.0, False),
    'AU6 Brick curb yellow':        ((215, 182, 100), 0.00, 0.00, 0, 1.0, False),
    'AU6 Concrete dark plinth':     ((58, 60, 62), 0.02, 0.10, 0, 1.0, False),
    'AU6 Concrete slabs':           ((178, 176, 170), 0.02, 0.10, 0, 1.0, False),
    'AU6 Concrete light':           ((190, 190, 185), 0.02, 0.10, 0, 1.0, False),
    'AU6 Concrete stone sill':      ((150, 150, 145), 0.03, 0.15, 0, 1.0, False),
    'AU6 Asphalt':                  ((88, 88, 90), 0.02, 0.05, 0, 1.0, False),
    'AU6 Paving footway':           ((165, 160, 150), 0.02, 0.05, 0, 1.0, False),
    # --- timber / paint
    'AU6 Timber rafters':           ((140, 80, 40), 0.03, 0.30, 0, 1.0, False),
    'AU6 Paint cream door':         ((230, 220, 185), 0.06, 0.55, 0, 1.0, False),
    'AU6 Paint white frames':       ((235, 235, 232), 0.06, 0.55, 0, 1.0, False),
    'AU6 Paint green timber':       ((30, 95, 60), 0.08, 0.60, 0, 1.0, False),
    'AU6 Paint pink birdhouse':     ((240, 140, 180), 0.05, 0.45, 0, 1.0, False),
    'AU6 Timber pallet pine':       ((185, 148, 102), 0.00, 0.00, 0, 1.0, False),
    'AU6 Timber pallet blocks':     ((155, 120, 80), 0.00, 0.00, 0, 1.0, False),
    'AU6 Timber weathered collar':  ((128, 98, 64), 0.00, 0.00, 0, 1.0, False),
    'AU6 Timber dark stained':      ((110, 70, 50), 0.03, 0.30, 0, 1.0, False),
    'AU6 Timber benches':           ((160, 105, 60), 0.03, 0.30, 0, 1.0, False),
    'AU6 OSB board':                ((200, 162, 108), 0.00, 0.00, 0, 1.0, False),
    'AU6 Sign yellow':              ((240, 210, 120), 0.05, 0.50, 0, 1.0, False),
    # --- landscape
    'AU6 Soil':                     ((52, 40, 30), 0.00, 0.00, 0, 1.0, False),
    'AU6 Mulch bark':               ((120, 90, 62), 0.00, 0.00, 0, 1.0, False),
    'AU6 Bark':                     ((92, 74, 60), 0.00, 0.00, 0, 1.0, False),
    'AU6 Foliage tree':             ((95, 140, 62), 0.00, 0.00, 0, 1.0, False),
    'AU6 Foliage shrub':            ((78, 118, 55), 0.00, 0.00, 0, 1.0, False),
    'AU6 Foliage planter':          ((72, 138, 66), 0.00, 0.00, 0, 1.0, False),
    'AU6 Grass':                    ((105, 150, 75), 0.00, 0.00, 0, 1.0, False),
    'AU6 Water':                    ((55, 110, 150), 0.30, 0.95, 0.40, 1.33, False),
    # --- context
    'AU6 Context massing':          ((215, 213, 208), 0.00, 0.00, 0, 1.0, False),
    'AU6 Context ground grey':      ((180, 175, 180), 0.00, 0.00, 0, 1.0, False),
}

LAYERS = {
    'ADDITIONS::Pavilion::Steel_Structure': 'AU6 Steel painted blue-grey',
    'ADDITIONS::Pavilion::Window_Frames': 'AU6 Aluminium satin',
    'ADDITIONS::Pavilion::Glazing': 'AU6 Glass clear',
    'ADDITIONS::Pavilion::Plinth': 'AU6 Concrete dark plinth',
    'ADDITIONS::Pavilion::Doors': 'AU6 Paint cream door',
    'ADDITIONS::Pavilion::Louvres_Grilles': 'AU6 Galvanised steel',
    'ADDITIONS::Pavilion::Fascia_Profiled_Sheet': 'AU6 Zinc / profiled sheet',
    'ADDITIONS::Pavilion::Roof': 'AU6 Roof membrane grey',
    'ADDITIONS::Pavilion::Rafters': 'AU6 Timber rafters',
    'ADDITIONS::Pavilion::Gutter_Downpipes': 'AU6 Zinc / profiled sheet',

    '07_OSM_Context::Buildings_3D': 'AU6 Context massing',
    '07_OSM_Context::Building_Parts_3D': 'AU6 Context massing',
    '07_OSM_Context::Roads_Main': 'AU6 Asphalt',
    '07_OSM_Context::Roads_Residential': 'AU6 Asphalt',
    '07_OSM_Context::Roads_Service': 'AU6 Asphalt',
    '07_OSM_Context::Footways_Pedestrian': 'AU6 Paving footway',
    '07_OSM_Context::Tram': 'AU6 Rail steel',
    '07_OSM_Context::Platforms': 'AU6 Concrete light',
    '07_OSM_Context::Green_Areas': 'AU6 Grass',
    '07_OSM_Context::Trees': 'AU6 Foliage tree',
    '07_OSM_Context::Water': 'AU6 Water',
    '07_OSM_Context::Landuse_Other': 'AU6 Context ground grey',
    '07_OSM_Context::Parking': 'AU6 Asphalt',

    '01_Existing_Buildings': 'AU6 Render beige east',          # main building mass 'Alfoldi utca 6-8'
    '01_Existing_Buildings::Courtyard_Facade_West_grey':'AU6 Render grey west',
    '01_Existing_Buildings::Courtyard_Facade_North_brick': 'AU6 Brick yellow north',
    '01_Existing_Buildings::Courtyard_Facade_East_beige': 'AU6 Render beige east',
    '01_Existing_Buildings::Facade_Paint_Patches': 'AU6 Paint white patch',
    '01_Existing_Buildings::Facade_Exposed_Brick': 'AU6 Brick exposed',
    '01_Existing_Buildings::Facade_Windows_Doors': 'AU6 Paint white frames',
    '01_Existing_Buildings::Facade_Window_Glass': 'AU6 Glass dark facade',
    '01_Existing_Buildings::Facade_Downpipes': 'AU6 Downpipe painted',
    '01_Existing_Buildings::Street_Wall': 'AU6 Render street wall',
    '01_Existing_Buildings::Street_Gate': 'AU6 Steel painted green',
    '01_Existing_Buildings::Brick_Hut': 'AU6 Brick red',
    '01_Existing_Buildings::Facade_Windows_Doors_Green_Timber': 'AU6 Paint green timber',
    '01_Existing_Buildings::Facade_Sills': 'AU6 Concrete stone sill',
    '01_Existing_Buildings::Facade_Render_Dark_Grey': 'AU6 Render dark grey',
    '01_Existing_Buildings::Facade_Render_Beige_Exposed': 'AU6 Render beige exposed',

    '02_Courtyard_Ground': 'AU6 Concrete slabs',
    '02_Courtyard_Ground::Walkway_Concrete_Slabs': 'AU6 Concrete slabs',
    '02_Courtyard_Ground::Garden_Bed_Mulch': 'AU6 Mulch bark',
    '02_Courtyard_Ground::Brick_Curb_Edging': 'AU6 Brick curb yellow',
    '02_Courtyard_Ground::Stepping_Slabs': 'AU6 Concrete slabs',
    '02_Courtyard_Ground::Soil_Mounds': 'AU6 Soil',
    '02_Courtyard_Ground::Asphalt_Yard': 'AU6 Asphalt',
    '02_Courtyard_Ground::Concrete_Apron': 'AU6 Concrete light',
    '02_Courtyard_Ground::Ramp_Platform_Steps': 'AU6 Concrete light',
    '02_Courtyard_Ground::Pallet_Planters::Pallet_Boards': 'AU6 Timber weathered collar',   # weathered (ref photos 2026-10-14)
    '02_Courtyard_Ground::Pallet_Planters::Pallet_Blocks': 'AU6 Timber weathered collar',
    '02_Courtyard_Ground::Pallet_Planters::Pallet_Collars': 'AU6 Timber weathered collar',
    '02_Courtyard_Ground::Pallet_Planters::Soil': 'AU6 Soil',
    '02_Courtyard_Ground::Pallet_Planters::Tubs_Pots': 'AU6 Plastic black',

    '03_Vegetation::Tree_Trunks_Branches': 'AU6 Bark',
    '03_Vegetation::Tree_Crowns': 'AU6 Foliage tree',
    '03_Vegetation::Shrubs': 'AU6 Foliage shrub',
    '03_Vegetation::Planter_Plants': 'AU6 Foliage planter',

    '04_Furniture_Elements::Brick_Fire_Pit': 'AU6 Brick fire pit',
    '04_Furniture_Elements::Metal_Stand': 'AU6 Steel painted dark',
    '04_Furniture_Elements::Birdhouse': 'AU6 Paint pink birdhouse',
    '04_Furniture_Elements::Handrails': 'AU6 Steel painted dark',
    '04_Furniture_Elements::Sheds::Corrugated_Roofs': 'AU6 Corrugated sheet rusty',
    '04_Furniture_Elements::Sheds::Steel_Structure': 'AU6 Steel painted dark',
    '04_Furniture_Elements::Sheds::OSB_Plywood_Walls': 'AU6 OSB board',
    '04_Furniture_Elements::Sheds::Curtains_Panels': 'AU6 Fabric black',
    '04_Furniture_Elements::Shelter_3_Gable::Galvanised_Frame': 'AU6 Galvanised steel',
    '04_Furniture_Elements::Shelter_3_Gable::Polycarbonate_Roof': 'AU6 Polycarbonate translucent',
    '04_Furniture_Elements::Shelter_3_Gable::Mesh_Panels': 'AU6 Steel mesh',
    '04_Furniture_Elements::WC_Entrance_Canopy': 'AU6 Timber dark stained',
    '04_Furniture_Elements::Fire_Ladder': 'AU6 Steel painted orange',
    '04_Furniture_Elements::Benches': 'AU6 Timber benches',
    '04_Furniture_Elements::Bins': 'AU6 Plastic green',
    '04_Furniture_Elements::Signs': 'AU6 Sign yellow',
}


def c(rgb):
    return Color.FromArgb(rgb[0], rgb[1], rgb[2])


# remove previous AU6 materials (re-run) - detach them from layers first
old = [rm for rm in doc.RenderMaterials if (rm.Name or '').startswith('AU6 ')]
if old:
    old_ids = set(rm.Id for rm in old)
    for L in doc.Layers:
        if not L.IsDeleted and L.RenderMaterial is not None and L.RenderMaterial.Id in old_ids:
            L.RenderMaterial = None
    for rm in old:
        doc.RenderMaterials.Remove(rm)

made = {}
for name, (rgb, refl, gloss, transp, ior, metal) in sorted(MATS.items()):
    m = Rhino.DocObjects.Material()
    m.Name = name
    m.DiffuseColor = c(rgb)
    m.AmbientColor = Color.Black
    m.Reflectivity = refl
    m.ReflectionGlossiness = gloss
    m.Shine = gloss * Rhino.DocObjects.Material.MaxShine
    m.SpecularColor = c(rgb) if metal else (Color.White if gloss > 0 else Color.Black)   # black = no highlight
    m.ReflectionColor = c(rgb) if metal else Color.White
    m.Transparency = transp
    if transp > 0:
        m.TransparentColor = c(rgb)
        m.IndexOfRefraction = ior
    rm = RenderMaterial.CreateBasicMaterial(m, doc)
    rm.Name = name
    doc.RenderMaterials.Add(rm)
    made[name] = rm

n_lay = 0
missing = []
for path, mname in sorted(LAYERS.items()):
    idx = doc.Layers.FindByFullPath(path, -1)
    if idx < 0:
        missing.append(path)
        continue
    doc.Layers[idx].RenderMaterial = made[mname]
    n_lay += 1

# make sure every object reads its material from its layer
n_obj = 0
s_ = Rhino.DocObjects.ObjectEnumeratorSettings()
s_.HiddenObjects = True
s_.LockedObjects = True
for o in doc.Objects.GetObjectList(s_):
    if o.Attributes.MaterialSource != Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer:
        a = o.Attributes.Duplicate()
        a.MaterialSource = Rhino.DocObjects.ObjectMaterialSource.MaterialFromLayer
        doc.Objects.ModifyAttributes(o, a, True)
        n_obj += 1

# the parked original pavilion placeholder (5 m box) caps the real pavilion in renders - keep it, but hidden
i_ph = doc.Layers.FindByFullPath('ADDITIONS::_superseded_placeholder', -1)
if i_ph >= 0:
    doc.Layers[i_ph].IsVisible = False

doc.Views.Redraw()
print('materials: %d  layers assigned: %d  objects switched to by-layer: %d' % (len(made), n_lay, n_obj))
if missing:
    print('missing layers: ' + '; '.join(missing))

#!/usr/bin/python
# -*- coding: utf-8 -*-

from progress import Progress

import math
import log
import os
import numpy as np
import numpy.linalg as la
import transformations as tm
from progress import Progress
from armature.utils import getMatrix
from exportutils.config import Config
from core import G


#----------------------------------------------------------------------
#   Config Dae by Chappellet Kevin
#----------------------------------------------------------------------



class ZTDaeConfig(Config):
    def __init__(self):
        from armature.options import ArmatureOptions

        Config.__init__(self)

        #Les 3 suivants dependent de l'export habituel, a corriger
        self.useTPose           = False
        self.feetOnGround       = True
        self.scale              = 1.0
        self.unit               = "dm"

        self.useRelPaths = False
        self.useNormals = True

        self.expressions = False
        self.useCustomTargets = False
        self.useTPose = False

        #Depend encore de l'export habituel, valeur a recuperer par defaut
        self.yUpFaceZ = False
        self.yUpFaceX = False
        self.zUpFaceNegY = True
        self.zUpFaceX = False

        self.localY = True  # exporter.localY.selected
        self.localX = False  # exporter.localX.selected
        self.localG = False  # exporter.localG.selected

        if not hasattr(G.app.selectedHuman, "getSkeleton"):
            self.rigOptions =  None
        else : 
            skel = G.app.selectedHuman.getSkeleton()
            if skel:
                self.rigOptions =  skel.options
            else:
                self.rigOptions =  None

        if not self.rigOptions:
            return
            self.rigOptions = ArmatureOptions()

        self.rigOptions.setExportOptions(
            useExpressions = self.expressions,
            useTPose = self.useTPose,
        )


#----------------------------------------------------------------------
#   library_controllers A modifier par la suite pour les animations, se baser sur la fonction presente dans MakeHuman
#----------------------------------------------------------------------

def writeLibraryControllers(fp, rmeshes, amt, config):
    fp.write('\n  <library_controllers/>\n')


#----------------------------------------------------------------------
#   library_geometry
#----------------------------------------------------------------------

def writeLibraryGeometry(fp, rmeshes, config):
    progress = Progress(len(rmeshes), None)
    fp.write('\n  <library_geometries>\n')
    for rmesh in rmeshes:
        if 'HighPolyEyes' != rmesh.name :
            writeGeometry(fp, rmesh, config)
            progress.step()
    fp.write('  </library_geometries>\n')


def rotateCoord(coord, config):
    offs = config.scale * config.offset
    coord = [co-offs for co in coord]
    if config.yUpFaceZ:
        pass
    elif config.yUpFaceX:
        coord = [(z,y,-x) for (x,y,z) in coord]
    elif config.zUpFaceNegY:
        coord = [(x,-z,y) for (x,y,z) in coord]
    elif config.zUpFaceX:
        coord = [(z,x,y) for (x,y,z) in coord]
    return coord


def writeGeometry(fp, rmesh, config):
    progress = Progress()
    progress(0)

    coord = rotateCoord(rmesh.getCoord(), config)
    nVerts = len(coord)

    fp.write('\n' +
        '    <geometry id="%sMesh" name="%s">\n' % (rmesh.name,rmesh.name) +
        '      <mesh>\n' +
        '        <source id="%s-Position">\n' % rmesh.name +
        '          <float_array count="%d" id="%s-Position-array">\n' % (3*nVerts,rmesh.name) +
        '          ')

    fp.write( ''.join([("%.4f %.4f %.4f " % tuple(co)) for co in coord]) )

    fp.write('\n' +
        '          </float_array>\n' +
        '          <technique_common>\n' +
        '            <accessor count="%d" source="#%s-Position-array" stride="3">\n' % (nVerts,rmesh.name) +
        '              <param type="float" name="X"></param>\n' +
        '              <param type="float" name="Y"></param>\n' +
        '              <param type="float" name="Z"></param>\n' +
        '            </accessor>\n' +
        '          </technique_common>\n' +
        '        </source>\n')
    progress(0.2)

    # Normals

    if config.useNormals:
        normals = rotateCoord(rmesh.getVnorm(), config)
        nNormals = len(normals)
        fp.write(
            '        <source id="%s-Normals">\n' % rmesh.name +
            '          <float_array count="%d" id="%s-Normals-array">\n' % (3*nNormals,rmesh.name) +
            '          ')

        fp.write( ''.join([("%.4f %.4f %.4f " % tuple(normalize(no))) for no in normals]) )

        fp.write('\n' +
            '          </float_array>\n' +
            '          <technique_common>\n' +
            '            <accessor count="%d" source="#%s-Normals-array" stride="3">\n' % (nNormals,rmesh.name) +
            '              <param type="float" name="X"></param>\n' +
            '              <param type="float" name="Y"></param>\n' +
            '              <param type="float" name="Z"></param>\n' +
            '            </accessor>\n' +
            '          </technique_common>\n' +
            '        </source>\n')
        progress(0.35)

    # UV coordinates

    texco = rmesh.getTexco()
    nUvVerts = len(texco)

    fp.write(
        '        <source id="%s-UV">\n' % rmesh.name +
        '          <float_array count="%d" id="%s-UV-array">\n' % (2*nUvVerts,rmesh.name) +
        '           ')

    fp.write( ''.join([("%.4f %.4f " % tuple(uv)) for uv in texco]) )

    fp.write('\n' +
        '          </float_array>\n' +
        '          <technique_common>\n' +
        '            <accessor count="%d" source="#%s-UV-array" stride="2">\n' % (nUvVerts,rmesh.name) +
        '              <param type="float" name="S"></param>\n' +
        '              <param type="float" name="T"></param>\n' +
        '            </accessor>\n' +
        '          </technique_common>\n' +
        '        </source>\n')
    progress(0.5, 0.7)

    # Faces

    fp.write(
        '        <vertices id="%s-Vertex">\n' % rmesh.name +
        '          <input semantic="POSITION" source="#%s-Position"/>\n' % rmesh.name +
        '        </vertices>\n')

    checkFaces(rmesh, nVerts, nUvVerts)
    progress(0.7, 0.9)
    #writePolygons(fp, rmesh, config)
    writePolylist(fp, rmesh, config)
    progress(0.9, 0.99)

    fp.write(
        '      </mesh>\n' +
        '    </geometry>\n')

    if rmesh.shapes:
        shaprog = Progress(len(rmesh.shapes))
        for name,shape in rmesh.shapes:
            writeShapeKey(fp, name, shape, rmesh, config)
            shaprog.step()

    progress(1)


def normalize(vec):
    vec = np.array(vec)
    return vec/math.sqrt(np.dot(vec,vec))


def writeShapeKey(fp, name, shape, rmesh, config):
    if len(shape.verts) == 0:
        log.debug("Shapekey %s has zero verts. Ignored" % name)
        return

    progress = Progress()

    # Verts

    progress(0)
    target = np.array(rmesh.getCoord())
    target[shape.verts] += shape.data[np.s_[...]]
    target = rotateCoord(target, config)
    nVerts = len(target)

    fp.write(
        '    <geometry id="%sMeshMorph_%s" name="%s">\n' % (rmesh.name, name, name) +
        '      <mesh>\n' +
        '        <source id="%sMeshMorph_%s-positions">\n' % (rmesh.name, name) +
        '          <float_array id="%sMeshMorph_%s-positions-array" count="%d">\n' % (rmesh.name, name, 3*nVerts) +
        '           ')

    fp.write( ''.join([("%.4f %.4f %.4f " % tuple(co)) for co in target]) )

    fp.write('\n' +
        '          </float_array>\n' +
        '          <technique_common>\n' +
        '            <accessor source="#%sMeshMorph_%s-positions-array" count="%d" stride="3">\n' % (rmesh.name, name, nVerts) +
        '              <param name="X" type="float"/>\n' +
        '              <param name="Y" type="float"/>\n' +
        '              <param name="Z" type="float"/>\n' +
        '            </accessor>\n' +
        '          </technique_common>\n' +
        '        </source>\n')
    progress(0.3)

    # Normals
    """
    fp.write(
'        <source id="%sMeshMorph_%s-normals">\n' % (rmesh.name, name) +
'          <float_array id="%sMeshMorph_%s-normals-array" count="18">\n' % (rmesh.name, name))
-0.9438583 0 0.3303504 0 0.9438583 0.3303504 0.9438583 0 0.3303504 0 -0.9438583 0.3303504 0 0 -1 0 0 1
    fp.write(
        '          </float_array>\n' +
        '          <technique_common>\n' +
        '            <accessor source="#%sMeshMorph_%s-normals-array" count="6" stride="3">\n' % (rmesh.name, name) +
        '              <param name="X" type="float"/>\n' +
        '              <param name="Y" type="float"/>\n' +
        '              <param name="Z" type="float"/>\n' +
        '            </accessor>\n' +
        '          </technique_common>\n' +
        '        </source>\n')
    """
    progress(0.6)

    # Polylist

    fvert = rmesh.getFvert()
    nFaces = len(fvert)

    fp.write(
        '        <vertices id="%sMeshMorph_%s-vertices">\n' % (rmesh.name, name) +
        '          <input semantic="POSITION" source="#%sMeshMorph_%s-positions"/>\n' % (rmesh.name, name) +
        '        </vertices>\n' +
        '        <polylist count="%d">\n' % nFaces +
        '          <input semantic="VERTEX" source="#%sMeshMorph_%s-vertices" offset="0"/>\n' % (rmesh.name, name) +
        #'          <input semantic="NORMAL" source="#%sMeshMorph_%s-normals" offset="1"/>\n' % (rmesh.name, name) +
        '          <vcount>')

    fp.write( ''.join(["4 " for fv in fvert]) )

    fp.write('\n' +
        '          </vcount>\n' +
        '          <p>')

    fp.write( ''.join([("%d %d %d %d " % (fv[0], fv[1], fv[2], fv[3])) for fv in fvert]) )

    fp.write('\n' +
        '          </p>\n' +
        '        </polylist>\n' +
        '      </mesh>\n' +
        '    </geometry>\n')
    progress(1)


#
#   writePolygons(fp, rmesh, config):
#   writePolylist(fp, rmesh, config):
#
'''
def writePolygons(fp, rmesh, config):
    fvert = rmesh.getFvert()
    fuvs = rmesh.getFuvs()

    fp.write(
        '        <polygons count="%d">\n' % len(fvert) +
        '          <input offset="0" semantic="VERTEX" source="#%s-Vertex"/>\n' % rmesh.name +
        '          <input offset="1" semantic="NORMAL" source="#%s-Normals"/>\n' % rmesh.name +
        '          <input offset="2" semantic="TEXCOORD" source="#%s-UV"/>\n' % rmesh.name)

    for fn,fvs in enumerate(fvert):
        fuv = fuvs[fn]
        fp.write('          <p>')
        for n,vn in enumerate(fvs):
            fp.write("%d %d %d " % (vn, vn, fuv[n]))
        fp.write('</p>\n')

    fp.write('\n' +
        '        </polygons>\n')
    return
'''

def writePolylist(fp, rmesh, config):
    progress = Progress(2)

    fvert = rmesh.getFvert()
    nFaces = len(fvert)

    fp.write(
        '        <polylist count="%d">\n' % nFaces +
        '          <input offset="0" semantic="VERTEX" source="#%s-Vertex"/>\n' % rmesh.name)

    if config.useNormals:
        fp.write(
        '          <input offset="1" semantic="NORMAL" source="#%s-Normals"/>\n' % rmesh.name +
        '          <input offset="2" semantic="TEXCOORD" source="#%s-UV"/>\n' % rmesh.name +
        '          <vcount>')
    else:
        fp.write(
        '          <input offset="1" semantic="TEXCOORD" source="#%s-UV"/>\n' % rmesh.name +
        '          <vcount>')

    fp.write( ''.join(["4 " for fv in fvert]) )

    fp.write('\n' +
        '          </vcount>\n'
        '          <p>')
    progress.step()

    fuvs = rmesh.getFuvs()

    for fn,fv in enumerate(fvert):
        fuv = fuvs[fn]
        if config.useNormals:
            fp.write( ''.join([("%d %d %d " % (fv[n], fn, fuv[n])) for n in range(4)]) )
        else:
            fp.write( ''.join([("%d %d " % (fv[n], fuv[n])) for n in range(4)]) )

    fp.write(
        '          </p>\n' +
        '        </polylist>\n')
    progress.step()

#
#   checkFaces(rmesh, nVerts, nUvVerts):
#

def checkFaces(rmesh, nVerts, nUvVerts):
    fvert = rmesh.getFvert()
    fuvs = rmesh.getFuvs()
    for fn,fvs in enumerate(fvert):
        for n,vn in enumerate(fvs):
            uv = fuvs[fn][n]
            if vn > nVerts:
                raise NameError("v %d > %d" % (vn, nVerts))
            if uv > nUvVerts:
                raise NameError("uv %d > %d" % (uv, nUvVerts))


#----------------------------------------------------------------------
#   library_images Pas d'image utilise
#----------------------------------------------------------------------

def writeLibraryImages(fp, rmeshes, config):
    progress = Progress(len(rmeshes), None)
    fp.write('\n  <library_images/>\n')

#----------------------------------------------------------------------
#   library_effects Configuration des effets (peut etre a modifier selon ce que l'on choisit)
#----------------------------------------------------------------------

def writeLibraryEffects(fp, rmeshes, config):
    fp.write('\n  <library_effects>\n')
    
    fp.write('    <effect id="young_asian_male_sweat-effect">\n' +
             '      <profile_COMMON>\n' +
             '         <technique sid="common">\n' +
             '           <phong>\n' +
             '              <emission>\n' +
             '                 <color sid="emission">0 0 0 1</color>\n'+
             '              </emission>\n' +
             '              <ambient>\n' +
             '                 <color sid="ambient">0 0 0 1</color>\n'+
             '              </ambient>\n' +
             '              <diffuse>\n' +
             '                 <color sid="diffuse">0.64 0.64 0.64 1</color>\n'+
             '              </diffuse>\n' +
             '              <specular>\n' +
             '                 <color sid="specular">0.09215 0.0902 0.07845 1</color>\n'+
             '              </specular>\n' +
             '              <shininess>\n' +
             '                 <float sid="shininess">204</float>\n'+
             '              </shininess>\n' +
             '              <index_of_refraction>\n' +
             '                 <float sid="index_of_refraction">1</float>\n'+
             '              </index_of_refraction>\n' +
             '           </phong>\n' +
             '         </technique>\n' +
             '      </profile_COMMON>\n' +
             '    </effect>\n')


    fp.write('  </library_effects>\n')

#----------------------------------------------------------------------
#   library_materials
#----------------------------------------------------------------------

def writeLibraryMaterials(fp, rmeshes, config):
    fp.write('\n  <library_materials>\n')
    
    fp.write('    <material id="young_asian_male_sweat-material" name="young_asian_male_sweat">\n' +
             '      <instance_effect url="#young_asian_male_sweat-effect"/>\n' +
             '    </material>\n')
        
    fp.write('  </library_materials>\n')


_Identity = np.identity(4, float)

#----------------------------------------------------------------------
#   library_visual_scenes
#----------------------------------------------------------------------

def writeLibraryVisualScenes(fp, rmeshes, amt, config):

    fp.write(
        '\n  <library_visual_scenes>\n' +
        '    <visual_scene id="Scene" name="Scene">\n')
    for rmesh in rmeshes:
        if 'HighPolyEyes' != rmesh.name :
            writeMeshNode(fp, "        ", rmesh, config)

    fp.write(
        '    </visual_scene>\n' +
        '  </library_visual_scenes>\n')


def writeSceneWithArmature(fp, rmeshes, amt, config):
    fp.write(
        '\n  <library_visual_scenes>\n' +
        '    <visual_scene id="Scene" name="Scene">\n')

    fp.write('      <node id="%s">\n' % amt.name)
    writeMatrix(fp, _Identity, "transform", "        ")
    for root in amt.hierarchy:
        writeBone(fp, root, [0,0,0], 'layer="L1"', "  ", amt, config)
    fp.write('      </node>\n')

    for rmesh in rmeshes:
        writeMeshArmatureNode(fp, "        ", rmesh, amt, config)

    fp.write(
        '    </visual_scene>\n' +
        '  </library_visual_scenes>\n')


def writeMeshArmatureNode(fp, pad, rmesh, amt, config):
    fp.write('\n%s<node id="%sObject" name="%s_%s">\n' % (pad, rmesh.name, amt.name, rmesh.name))
    writeMatrix(fp, _Identity, "transform", pad+"  ")
    fp.write(
        '%s  <instance_controller url="#%s-skin">\n' % (pad, rmesh.name) +
        '%s    <skeleton>#%sSkeleton</skeleton>\n' % (pad, amt.roots[0].name))
    writeBindMaterial(fp, pad, rmesh.material)
    fp.write(
        '%s  </instance_controller>\n' % pad +
        '%s</node>\n' % pad)


def writeMeshNode(fp, pad, rmesh, config):
    fp.write('\n%s<node id="%sObject" name="%s">\n' % (pad, rmesh.name, rmesh.name))
    writeMatrix(fp, _Identity, "transform", pad+"  ")
    fp.write(
        '%s  <instance_geometry url="#%sMesh">\n' % (pad, rmesh.name))
    writeBindMaterial(fp, pad, rmesh.material)
    fp.write(
        '%s  </instance_geometry>\n' % pad +
        '%s</node>\n' % pad)


def writeBindMaterial(fp, pad, mat):
    matname = mat.name.replace(" ", "_")
    fp.write(
        '%s    <bind_material>\n' % pad +
        '%s      <technique_common>\n' % pad +
        '%s        <instance_material symbol="young_asian_male_sweat-material" target="#young_asian_male_sweat-material"/>\n' +
        '%s      </technique_common>\n' % pad +
        '%s    </bind_material>\n' % pad)


def writeBone(fp, hier, orig, extra, pad, amt, config):
    (bone, children) = hier
    bname = goodBoneName(bone.name)
    if bone:
        nameStr = 'sid="%s"' % bname
        idStr = 'id="%s" name="%s"' % (bname, bname)
    else:
        nameStr = ''
        idStr = ''

    fp.write('%s      <node %s %s type="JOINT" %s>\n' % (pad, extra, nameStr, idStr))
    relmat = bone.getRelativeMatrix(config)
    writeMatrix(fp, relmat, "transform", pad+"        ")
    for child in children:
        writeBone(fp, child, bone.head, '', pad+'  ', amt, config)
    fp.write('%s      </node>\n' % pad)


def writeMatrix(fp, mat, sid, pad):
    fp.write('%s<matrix sid="%s">\n' % (pad, sid))
    for i in range(4):
        fp.write('%s  %.5f %.5f %.5f %.5f\n' % (pad, mat[i][0], mat[i][1], mat[i][2], mat[i][3]))
    fp.write('%s</matrix>\n' % pad)


# To avoid error message about Sax FWL Error in Blender
def goodBoneName(bname):
    return bname.replace(".","_")



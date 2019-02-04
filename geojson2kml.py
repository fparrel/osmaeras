#!/usr/bin/env python

from lxml import etree as ET
import sys
import os

def usage():
    print('Usage: %s input.geojson' % sys.argv[0])

def main():
    if len(sys.argv)!=2 or sys.argv[1] in ('-h','--help'):
        usage()
        return
    input = sys.argv[1]
    basename = input.strip('.geojson')
    wo_colors_fname = '%s_wo_colors.kml' % basename
    with_colors_fname = '%s.kml' % basename
    cmd = "ogr2ogr -f 'KML' %s %s" % (wo_colors_fname, input)
    os.system(cmd)

    tree = ET.parse(open(wo_colors_fname,'r'))
    root = tree.getroot()

    placemarks = []

    colortorgb = {'grey':'88888888','green':'88008214','yellow':'8814f0ff','red':'ee0000ff'}

    for placemark in root[0].find('Folder', namespaces = root.nsmap).findall('Placemark', namespaces = root.nsmap):
        d = placemark.find('ExtendedData/SchemaData/SimpleData', namespaces = root.nsmap)
        assert(d.attrib.get('name')=='color')
        color = d.text
        style = ET.Element('Style')
        linestyle = ET.SubElement(style,'LineStyle')
        polystyle = ET.SubElement(style, 'PolyStyle')
        colline = ET.SubElement(linestyle, 'color')
        colline.text = colortorgb[color]
        colpoly = ET.SubElement(polystyle, 'color')
        colpoly.text = colortorgb[color]
        fill = ET.SubElement(polystyle, 'fill')
        outline = ET.SubElement(polystyle, 'outline')
        if color=='red': # red if for outline only
            fill.text = '0'
            outline.text = '1'
        else:
            fill.text = '1'
            outline.text = '0'
        p = placemark.find('Polygon', namespaces = root.nsmap)
        if p!=None: # ignore other than polygons
            pm = ET.Element('Placemark')
            pm.append(style)
            pm.append(p)
            placemarks.append(pm)

    folder = tree.getroot()[0].find('Folder', namespaces = root.nsmap)
    name = folder.find('name', namespaces = root.nsmap)
    folder.clear()
    folder.append(name)
    for pm in placemarks:
        folder.append(pm)

    tree.write(with_colors_fname)

if __name__=='__main__':
    main()

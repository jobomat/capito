//Maya ASCII 2022 scene
//Name: ik_fk_icon.ma
//Last modified: Fri, Nov 05, 2021 09:51:34 AM
//Codeset: 1252
requires maya "2022";
requires "mtoa" "4.2.4";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2022";
fileInfo "version" "2022";
fileInfo "cutIdentifier" "202108111415-612a77abf4";
fileInfo "osv" "Windows 10 Enterprise LTSC 2019 v1809 (Build: 17763)";
fileInfo "UUID" "CEF4C4B6-4F2F-B0AC-ECBA-539B77EF57BC";
fileInfo "license" "education";
createNode transform -n "ik_fk_offset_grp";
	rename -uid "EB737CC6-4017-9E9E-747F-AF94F4DC8143";
	setAttr ".t" -type "double3" 1 1 1 ;
	setAttr ".r" -type "double3" 1 1 1 ;
createNode transform -n "ik_fk_ctrl" -p "ik_fk_offset_grp";
	rename -uid "27ED2B52-443D-FB97-BA41-B09FC313412D";
	addAttr -ci true -k true -sn "ik_fk" -ln "ik_fk" -min 0 -max 1 -at "float";
	setAttr -l on -k off ".v";
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -l on -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
	setAttr -k on ".ik_fk";
createNode nurbsCurve -n "ik_fk_ctrlShape" -p "ik_fk_ctrl";
	rename -uid "F86600C7-427C-98D2-4B5C-68B2DD071FE7";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".tw" yes;
createNode nurbsCurve -n "ik_fk_ctrlShape1" -p "ik_fk_ctrl";
	rename -uid "E59549AB-476B-8782-385C-91997886921E";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".tw" yes;
createNode nurbsCurve -n "ik_fk_ctrlShape2" -p "ik_fk_ctrl";
	rename -uid "3E117149-493A-4446-CA55-0A97FB405670";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".tw" yes;
createNode nurbsCurve -n "ik_fk_ctrlShape3" -p "ik_fk_ctrl";
	rename -uid "293B4D0D-4E6A-347F-138F-64B3433ACC0A";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".tw" yes;
createNode nurbsCurve -n "ik_fk_ctrlShapeOrig" -p "ik_fk_ctrl";
	rename -uid "036933C5-47E6-FB50-F221-309479EC68CB";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 4 0 no 3
		5 0 2.2000000000000002 2.8999999999999999 5.0999999999999996 5.7999999999999998
		
		5
		-0.99717685611700002 -0.699958102586 0
		-0.99717685611700002 0.69994944218099997 0
		-0.55175172823700003 0.69994944218099997 0
		-0.55175172823700003 -0.699958102586 0
		-0.99717685611700002 -0.699958102586 0
		;
createNode nurbsCurve -n "ik_fk_ctrlShape1Orig" -p "ik_fk_ctrl";
	rename -uid "BC0E6F23-4E14-F06C-1F09-388AE9B33799";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 11 0 no 3
		12 0 1.23627251439 2.2487727051199999 2.9487727051200001 5.1487727051199998
		 5.84877270512 6.7722090368499996 7.9151238344000001 8.6713731668200005 10.0035915986
		 11.4904891913 12.2826765721
		12
		0.59959277816300005 -0.699958102586 0
		0.14820204414300001 -0.055682349816899998 0
		0.14820204414300001 -0.699958102586 0
		-0.29722308373700002 -0.699958102586 0
		-0.29722308373700002 0.69994944218099997 0
		0.14820204414300001 0.69994944218099997 0
		0.14820204414300001 0.112346947681 0
		0.57672559228300002 0.69994944218099997 0
		1.05794338599 0.69994944218099997 0
		0.52005330497299995 0.044737715799899998 0
		1.1036787287200001 -0.699958102586 0
		0.59959277816300005 -0.699958102586 0
		;
createNode nurbsCurve -n "ik_fk_ctrlShape2Orig" -p "ik_fk_ctrl";
	rename -uid "0D7E124C-4DF2-D6BD-94E9-BBBE632A6F17";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 10 0 no 3
		11 0 0.5 1.43750057221 1.83750057221 2.77500114443 3.6750011444299999 4.3750011444299997
		 6.5750011444299998 8.2515648126999999 8.6515648127000002 9.6281284809599992
		11
		0.072322092643199998 -0.70054907269699995 0
		0.072322092643199998 -0.700341201681 0
		0.071932334253200003 -0.700341201681 0
		0.071932334253200003 -0.70017490486800005 0
		0.072322092643199998 -0.70017490486800005 0
		0.072322092643199998 -0.69980073703900003 0
		0.072613112073199995 -0.69980073703900003 0
		0.072613112073199995 -0.70071536951000002 0
		0.071916094083200002 -0.70071536951000002 0
		0.071916094083200002 -0.70054907269699995 0
		0.072322092643199998 -0.70054907269699995 0
		;
createNode nurbsCurve -n "ik_fk_ctrlShape3Orig" -p "ik_fk_ctrl";
	rename -uid "E0C50C7A-4950-D5DB-30EA-50B79A41E775";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".ove" yes;
	setAttr ".ovrgbf" yes;
	setAttr ".ovrgb" -type "float3" 0 1 1 ;
	setAttr ".cc" -type "nurbsCurve" 
		1 11 0 no 3
		12 0 1.23627251439 2.2487727051199999 2.9487727051200001 5.1487727051199998
		 5.84877270512 6.7722090368499996 7.9151238344000001 8.6713731668200005 10.0035915986
		 11.4904891913 12.2826765721
		12
		0.071237265723199994 -0.69980073703900003 0
		0.071532182783200005 -0.70022167592600004 0
		0.071532182783200005 -0.69980073703900003 0
		0.071823202203200001 -0.69980073703900003 0
		0.071823202203200001 -0.70071536951000002 0
		0.071532182783200005 -0.70071536951000002 0
		0.071532182783200005 -0.70033145821300002 0
		0.071252206043199998 -0.70071536951000002 0
		0.070937801413199997 -0.70071536951000002 0
		0.071289233003200003 -0.70028728558200004 0
		0.070907920133200006 -0.69980073703900003 0
		0.071237265723199994 -0.69980073703900003 0
		;
createNode blendShape -n "ik_fk_bs";
	rename -uid "E76F5A13-4B05-67B7-6BED-258199771E0A";
	addAttr -ci true -h true -sn "aal" -ln "attributeAliasList" -dt "attributeAlias";
	setAttr -s 4 ".ip";
	setAttr -s 4 ".og";
	setAttr -s 4 ".orggeom";
	setAttr -s 4 ".it";
	setAttr ".it[0].itg[0].iti[6000].ipt" -type "pointArray" 5 1.0508223981649001
		 1.406905318085 0 1 1.0508223981649001 0.0064718813280000287 0 1 0.60522994101490002
		 0.0064718813280000287 0 1 0.60522994101490002 1.406905318085 0 1 1.0508223981649001
		 1.406905318085 0 1 ;
	setAttr ".it[0].itg[0].iti[6000].ict" -type "componentList" 1 "cv[0:4]";
	setAttr ".it[1].itg[0].iti[6000].ipt" -type "pointArray" 12 -0.54654708169510002
		 1.406905318085 0 1 -0.094986777355099999 0.76238753543589999 0 1 -0.094986777355099999
		 1.406905318085 0 1 0.35060567978490004 1.406905318085 0 1 0.35060567978490004 0.0064718813280000287
		 0 1 -0.094986777355099999 0.0064718813280000287 0 1 -0.094986777355099999 0.59429511572800009
		 0 1 -0.52367130548509999 0.0064718813280000287 0 1 -1.0050698744021 0.0064718813280000287
		 0 1 -0.46697772855509995 0.66192974581909991 0 1 -1.0508223981621001 1.406905318085
		 0 1 -0.54654708169510002 1.406905318085 0 1 ;
	setAttr ".it[1].itg[0].iti[6000].ict" -type "componentList" 1 "cv[0:11]";
	setAttr ".it[2].itg[0].iti[6000].ipt" -type "pointArray" 11 -0.85451637127519997
		 1.144045868726 0 1 -0.85451637127519997 0.82774137317999996 0 1 -0.26144508015520002
		 0.82774137317999996 0 1 -0.26144508015520002 0.57469777674700007 0 1 -0.85451637127519997
		 0.57469777674700007 0 1 -0.85451637127519997 0.005349684778000019 0 1 -1.2973426650432001
		 0.005349684778000019 0 1 -1.2973426650432001 1.397089465159 0 1 -0.23673341436520001
		 1.397089465159 0 1 -0.23673341436520001 1.144045868726 0 1 -0.85451637127519997 1.144045868726
		 0 1 ;
	setAttr ".it[2].itg[0].iti[6000].ict" -type "componentList" 1 "cv[0:10]";
	setAttr ".it[3].itg[0].iti[6000].ipt" -type "pointArray" 12 0.79619780532679996
		 0.005349684778000019 0 1 0.34744071178480002 0.64586640891500002 0 1 0.34744071178480002
		 0.005349684778000019 0 1 -0.095385581975300004 0.005349684778000019 0 1 -0.095385581975300004
		 1.397089465159 0 1 0.34744071178480002 1.397089465159 0 1 0.34744071178480002 0.81291533901200008
		 0 1 0.77346403810779996 1.397089465159 0 1 1.2518741652968 1.397089465159 0 1 0.71712240541479999
		 0.74570057338100004 0 1 1.2973426650368001 0.005349684778000019 0 1 0.79619780532679996
		 0.005349684778000019 0 1 ;
	setAttr ".it[3].itg[0].iti[6000].ict" -type "componentList" 1 "cv[0:11]";
	setAttr ".mlid" 0;
	setAttr ".mlpr" 0;
	setAttr ".pndr[0]"  0;
	setAttr ".tgdt[0].cid" -type "Int32Array" 1 0 ;
	setAttr ".aal" -type "attributeAlias" {"ik_fk_ctrl","weight[0]"} ;
select -ne :time1;
	setAttr ".o" 1;
	setAttr ".unw" 1;
select -ne :hardwareRenderingGlobals;
	setAttr ".otfna" -type "stringArray" 22 "NURBS Curves" "NURBS Surfaces" "Polygons" "Subdiv Surface" "Particles" "Particle Instance" "Fluids" "Strokes" "Image Planes" "UI" "Lights" "Cameras" "Locators" "Joints" "IK Handles" "Deformers" "Motion Trails" "Components" "Hair Systems" "Follicles" "Misc. UI" "Ornaments"  ;
	setAttr ".otfva" -type "Int32Array" 22 0 1 1 1 1 1
		 1 1 1 0 0 0 0 0 0 0 0 0
		 0 0 0 0 ;
	setAttr ".fprt" yes;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 5 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultRenderGlobals;
	setAttr ".ren" -type "string" "arnold";
select -ne :defaultResolution;
	setAttr ".pa" 1;
select -ne :defaultColorMgtGlobals;
	setAttr ".cfe" yes;
	setAttr ".cfp" -type "string" "C:/OCIO/aces_1.1/config.ocio";
	setAttr ".vtn" -type "string" "sRGB (ACES)";
	setAttr ".vn" -type "string" "sRGB";
	setAttr ".dn" -type "string" "ACES";
	setAttr ".wsn" -type "string" "ACES - ACEScg";
	setAttr ".otn" -type "string" "sRGB (ACES)";
	setAttr ".potn" -type "string" "sRGB (ACES)";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
connectAttr "ik_fk_bs.og[0]" "ik_fk_ctrlShape.cr";
connectAttr "ik_fk_bs.og[1]" "ik_fk_ctrlShape1.cr";
connectAttr "ik_fk_bs.og[2]" "ik_fk_ctrlShape2.cr";
connectAttr "ik_fk_bs.og[3]" "ik_fk_ctrlShape3.cr";
connectAttr "ik_fk_ctrlShapeOrig.ws" "ik_fk_bs.ip[0].ig";
connectAttr "ik_fk_ctrlShape1Orig.ws" "ik_fk_bs.ip[1].ig";
connectAttr "ik_fk_ctrlShape2Orig.ws" "ik_fk_bs.ip[2].ig";
connectAttr "ik_fk_ctrlShape3Orig.ws" "ik_fk_bs.ip[3].ig";
connectAttr "ik_fk_ctrlShapeOrig.l" "ik_fk_bs.orggeom[0]";
connectAttr "ik_fk_ctrlShape1Orig.l" "ik_fk_bs.orggeom[1]";
connectAttr "ik_fk_ctrlShape2Orig.l" "ik_fk_bs.orggeom[2]";
connectAttr "ik_fk_ctrlShape3Orig.l" "ik_fk_bs.orggeom[3]";
connectAttr "ik_fk_ctrl.ik_fk" "ik_fk_bs.w[0]";
// End of ik_fk_icon.ma

## A cardboard box model

I downloaded cardboard box model [from Sketchfab](https://sketchfab.com/3d-models/cardboard-box-58db7bc84fe64eb990f851b9e50fab5c):
![alt text](images/sketchfab_original.png)

The model came in the `.fbx` format but Webots can only open Collada (`.dae`) or Wavefront (`.obj`) files. I used Blender to import the `.fbx` file, assign the available textures and export it in the Wavefront format. However, when I loaded the model in Webots, the model looked dull, and unlike the Sketchfab preview. I suspected the texture files were not being loaded correctly. I'm inexperienced with 3D mesh modeling and texturing, so I had trouble understanding the purpose of each file. There were 4 png texture files:

- BaseColor
- Roughness
- Normal
- Height

A Google search lead me to a relevant [Robotics Stackexchange post](https://robotics.stackexchange.com/questions/24932/cant-make-new-cadshape-models-have-the-same-appearance-as-previous-pbrappearanc). This post made me think that out of the two formats that Webots is capable of loading (Wavefront and Collada), I would probably have better chances with the Wavefront file if I wanted to be able to use these textures.

## The Wavefront format

After loading the `.fbx` in Blender I had something like this:
![alt text](images/blender_map.png)

When Blender exports a model in the Wavefront format, it creates a `.obj` and a `.mtl` file. The ``mtl` file is a materials file which looks like this:

```
# Blender 4.1.1 MTL File: 'box.blend'
# www.blender.org

newmtl Material1
Ks 0.500000 0.500000 0.500000
Ke 0.000000 0.000000 0.000000
Ni 1.500000
d 1.000000
illum 2
Pm 0.000000
Ps 0.000000
Pc 0.000000
Pcr 0.030000
aniso 0.000000
anisor 0.000000
map_Kd CardboardBox_Low_DefaultMaterial_BaseColor.png
map_Pr textures/CardboardBox_Low_DefaultMaterial_Roughness.png
map_Bump -bm 1.000000 textures/CardboardBox_Low_DefaultMaterial_Normal.png
```

The `.obj` file references the .mtl file, and when Webots' `CadShape` node loads the Wavefront file, it parses the .mtl file and extracts the material information.

Here are the lines that point to the files I defined in Blender:
```
map_Kd textures/CardboardBox_Low_DefaultMaterial_BaseColor.png
map_Pr textures/CardboardBox_Low_DefaultMaterial_Roughness.png
map_Bump -bm 1.000000 textures/CardboardBox_Low_DefaultMaterial_Normal.png
```

For some reason the Height file was not referenced.

The first problem I encountered was this warning from Webots, and no box model shown:
```
WARNING: CardboardBox2 "solid" > Transform  > CadShape : Invalid data, please verify mesh file: Cannot parse string "niso" as a real number: does not start with digit or decimal point followed by digit.
```

This was easy to solve, I just deleted the following two lines from the `.obj` file:
```
aniso 0.000000
anisor 0.000000
```

The model loaded without further warnings, but it still didn't look right. By deleting each of these lines one by one and reloading the simulation, I saw the effect of each on the rendered model.


1) The box using only the mapped BaseColor texture:
![alt text](images/BaseColor.png)

2) The box using the mapped BaseColor texture and the mapped Roughness texture:
![alt text](images/Basecolor_and_Roughness.png)

3) The box using the mapped BaseColor and Normal textures didn’t show any difference .


## Inspecting the Webots CAD loading code

To understand why the Normal texture wasn't affecting the appearance, I inspected the C++ Webots code for the `CadShape` component. I found that four arrays were being filled with data from the loaded CAD file:

```C++
for (size_t j = 0; j < mesh->mNumVertices; ++j) {
    
    // extract the coordinate
    const aiVector3D vertice = transform * mesh->mVertices[j];
    coordData[currentCoordIndex++] = vertice[0];
    ...
    
    // extract the normal
    const aiVector3D normal = transform * mesh->mNormals[j];
    normalData[currentNormalIndex++] = normal[0];
    ...
    
    // extract the texture coordinate
    if (mesh->HasTextureCoords(0)) {
        texCoordData[currentTexCoordIndex++] = mesh->mTextureCoords[0][j].x;
        ...
    } 
    ...

    // create the index array
    for (size_t j = 0; j < mesh->mNumFaces; ++j) {
        const aiFace face = mesh->mFaces[j];
        ...
        indexData[currentIndexIndex++] = face.mIndices[0];
        ...
    }
}
```
(Modified for brevity from the [Webots CadShape code](https://github.com/cyberbotics/webots/blob/1c6c9a38e7351d3c586e15ff039b26aa53033a7b/src/webots/nodes/WbCadShape.cpp#L440))

The code appears to load mesh vertices, mesh normals, one texture map and faces indices. Despite the normals map data being loaded, it didn’t affect the model's appearance. Why I don't see any difference when using it? And, which part of the code is really loading the `mesh` data?

Looking through the Webots code [I found](https://github.com/cyberbotics/webots/blob/1c6c9a38e7351d3c586e15ff039b26aa53033a7b/dependencies/Makefile.linux#L13) that Webots uses the Assimp library to load CAD data. Searching Assimp's GitHub issues related to .obj files and normal maps, I found several issues: [issue 1](https://github.com/assimp/assimp/issues/1121) [issue 2](https://github.com/assimp/assimp/issues/430), [issue 3](https://github.com/assimp/assimp/issues/3726). There I discovered that changing `map_Bump` to either `Map_Kn` or `norm` resolved the issue:


![BaseColor, Roughness and Normal](images/BaseColor_Roughness_and_Normal.png)

The texture mapping lines now looked like this:
```
map_Kd textures/CardboardBox_Low_DefaultMaterial_BaseColor.png
map_Pr textures/CardboardBox_Low_DefaultMaterial_Roughness.png
norm textures/CardboardBox_Low_DefaultMaterial_Normal.png
```

I tried using the available height texture with the following line, but it had no effect:
```
disp textures/CardboardBox_Low_DefaultMaterial_Height.png
```

I don't think that Webots it's able to load this type of texture. I might be wrong, but the Stackexchange post mentioned that the Webots [PBRAppearance](https://cyberbotics.com/doc/reference/pbrappearance) node allows more control than `CadShape`, listing the following supported texture maps, where there is no height or bump texture mentioned.

- baseColorMap
- roughnessMap
- metalnessMap
- normalMap
- occlusionMap
- emissiveColorMap


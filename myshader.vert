#version 150

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;

out vec2 tex_coord;

uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
  gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
  tex_coord = p3d_MultiTexCoord0;
}
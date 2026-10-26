using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public class BuildScript
{
    public static void CreateMaterials()
    {
        Debug.Log("[FARS] Setting up materials and shaders...");
        if (!AssetDatabase.IsValidFolder("Assets/Resources"))
        {
            AssetDatabase.CreateFolder("Assets", "Resources");
        }

        Shader litShader = Shader.Find("Universal Render Pipeline/Lit");
        if (litShader == null) litShader = Shader.Find("Universal Render Pipeline/Unlit");
        if (litShader == null) litShader = Shader.Find("Standard");

        Debug.Log($"[FARS] Primary Shader: {litShader?.name}");
        if (litShader != null)
        {
            Material mat = new Material(litShader);
            mat.name = "FARS_BaseMaterial";
            AssetDatabase.CreateAsset(mat, "Assets/Resources/FARS_BaseMaterial.mat");
        }

        Shader unlitShader = Shader.Find("Universal Render Pipeline/Unlit");
        if (unlitShader == null) unlitShader = Shader.Find("Sprites/Default");
        if (unlitShader != null)
        {
            Material unlitMat = new Material(unlitShader);
            unlitMat.name = "FARS_UnlitMaterial";
            AssetDatabase.CreateAsset(unlitMat, "Assets/Resources/FARS_UnlitMaterial.mat");
        }

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("[FARS] Materials saved to Assets/Resources successfully.");
    }

    public static void BuildWindows()
    {
        CreateMaterials();

        Debug.Log("[FARS] Starting Windows 64-bit Player Build...");
        BuildPlayerOptions buildPlayerOptions = new BuildPlayerOptions();
        buildPlayerOptions.scenes = new[] { "Assets/Scenes/SampleScene.unity" };
        buildPlayerOptions.locationPathName = @"D:/fyeshi/project/rohit/unity_build/FARS_Unity.exe";
        buildPlayerOptions.target = BuildTarget.StandaloneWindows64;
        buildPlayerOptions.options = BuildOptions.None;

        BuildReport report = BuildPipeline.BuildPlayer(buildPlayerOptions);
        BuildSummary summary = report.summary;

        if (summary.result == BuildResult.Succeeded)
        {
            Debug.Log($"[FARS] Build succeeded! Total size: {summary.totalSize} bytes");
            EditorApplication.Exit(0);
        }
        else
        {
            Debug.LogError($"[FARS] Build failed with result: {summary.result}");
            EditorApplication.Exit(1);
        }
    }
}

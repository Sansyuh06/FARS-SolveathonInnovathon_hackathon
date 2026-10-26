using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public class BuildScript
{
    public static void BuildWindows()
    {
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

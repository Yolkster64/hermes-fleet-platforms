// HermesCSharpLearning.cs
// C# core for Hermes agent learning
using System;
using System.Runtime.InteropServices;

public class HermesCSharpLearning {
    [DllExport("TrainSkill", CallingConvention = CallingConvention.Cdecl)]
    public static double TrainSkill([In] double[] data, int len) {
        double sum = 0;
        for (int i = 0; i < len; ++i) sum += data[i];
        return Math.Sqrt(sum);
    }
}
// Add more ML algorithms here (e.g., SVM, KMeans, DecisionTree)

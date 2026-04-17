using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace HELIOS.Platform.Presentation.Views;

public sealed partial class HelpPage : Page
{
    public HelpPage()
    {
        this.InitializeComponent();
    }
}

public class BulletList : StackPanel
{
    public BulletList()
    {
        Spacing = 5;
    }
}

public class ListItem : TextBlock
{
    public ListItem()
    {
        Margin = new Thickness(20, 0, 0, 0);
    }
}

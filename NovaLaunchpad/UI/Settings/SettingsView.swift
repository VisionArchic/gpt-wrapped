import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var settings: UserSettings
    
    var body: some View {
        Form {
            Section(header: Text("Grid")) {
                Stepper("Rows: \(settings.gridRows)", value: $settings.gridRows, in: 3...8)
                Stepper("Columns: \(settings.gridColumns)", value: $settings.gridColumns, in: 4...12)
                Slider(value: $settings.iconSize, in: 32...128) {
                    Text("Icon Size")
                }
            }
            
            Section(header: Text("Appearance")) {
                Text("Theme settings (Not implemented)")
            }
            
            Section(header: Text("Behavior")) {
                Text("Hotkeys (Not implemented)")
            }
            
            Button("Quit NovaLaunchpad") {
                NSApplication.shared.terminate(nil)
            }
        }
        .padding()
    }
}

import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = LauncherViewModel()
    @EnvironmentObject var settings: UserSettings
    @State private var showSettings = false
    
    var body: some View {
        VStack(spacing: 0) {
            SearchBar(text: $viewModel.searchText)
                .onChange(of: viewModel.searchText) {
                    viewModel.filterApps()
                }
            
            GridView(viewModel: viewModel)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            
            HStack {
                Spacer()
                Button(action: { showSettings.toggle() }) {
                    Image(systemName: "gear")
                        .font(.system(size: 20))
                        .foregroundColor(.white.opacity(0.8))
                }
                .buttonStyle(PlainButtonStyle())
                .padding()
                .popover(isPresented: $showSettings) {
                    SettingsView()
                        .frame(width: 300, height: 400)
                }
            }
        }
        .onAppear {
            // Trigger initial reflow based on settings
             viewModel.reflowPages(rows: settings.gridRows, cols: settings.gridColumns)
             GlobalHotkeys.shared.register()
             
             // Local event monitor for arrows/esc
             NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
                 if event.keyCode == 53 { // Esc
                     if !viewModel.searchText.isEmpty {
                         viewModel.searchText = ""
                         return nil
                     } else {
                         NSApplication.shared.hide(nil)
                         return nil
                     }
                 }
                 
                 // Arrows
                 // 123: left, 124: right, 125: down, 126: up
                 switch event.keyCode {
                 case 123: viewModel.navigateSelection(.left, cols: settings.gridColumns); return nil
                 case 124: viewModel.navigateSelection(.right, cols: settings.gridColumns); return nil
                 case 125: viewModel.navigateSelection(.down, cols: settings.gridColumns); return nil
                 case 126: viewModel.navigateSelection(.up, cols: settings.gridColumns); return nil
                 case 36: // Enter
                    viewModel.launchSelected()
                    return nil
                 default:
                     return event
                 }
             }
        }
        .onChange(of: settings.gridColumns) {
             viewModel.reflowPages(rows: settings.gridRows, cols: settings.gridColumns)
        }
        .onChange(of: settings.gridRows) {
             viewModel.reflowPages(rows: settings.gridRows, cols: settings.gridColumns)
        }
    }
}

// Helper for blur background
struct VisualEffectView: NSViewRepresentable {
    var material: NSVisualEffectView.Material
    var blendingMode: NSVisualEffectView.BlendingMode

    func makeNSView(context: Context) -> NSVisualEffectView {
        let visualEffectView = NSVisualEffectView()
        visualEffectView.material = material
        visualEffectView.blendingMode = blendingMode
        visualEffectView.state = .active
        return visualEffectView
    }

    func updateNSView(_ nsView: NSVisualEffectView, context: Context) {
        nsView.material = material
        nsView.blendingMode = blendingMode
    }
}

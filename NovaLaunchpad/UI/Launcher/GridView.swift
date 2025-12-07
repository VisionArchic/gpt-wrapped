import SwiftUI

struct GridView: View {
    @ObservedObject var viewModel: LauncherViewModel
    @EnvironmentObject var settings: UserSettings
    
    var body: some View {
        GeometryReader { geometry in
            if viewModel.isSearching {
                // Single scrollable grid for search results
                ScrollView {
                    LazyVGrid(columns: gridColumns, spacing: 20) {
                        ForEach(viewModel.filteredApps) { app in
                            AppIconView(item: app, 
                                       size: settings.iconSize, 
                                       isSelected: viewModel.selectedAppID == app.bundleIdentifier)
                                .onTapGesture {
                                    openApp(app)
                                }
                        }
                    }
                    .padding(40)
                }
            } else {
                // Custom Paged View for macOS
                GeometryReader { geo in
                    HStack(spacing: 0) {
                        ForEach(0..<viewModel.pages.count, id: \.self) { index in
                            makePage(viewModel.pages[index])
                                .frame(width: geo.size.width, height: geo.size.height)
                        }
                    }
                    .offset(x: -CGFloat(viewModel.currentPageIndex) * geo.size.width)
                    .animation(.spring(response: 0.3, dampingFraction: 0.8), value: viewModel.currentPageIndex)
                }
            }
        }
    }
    
    // Page indicators
    private func pageIndicators(count: Int) -> some View {
        HStack(spacing: 8) {
            ForEach(0..<count, id: \.self) { index in
                Circle()
                    .fill(index == viewModel.currentPageIndex ? Color.white : Color.white.opacity(0.3))
                    .frame(width: 8, height: 8)
                    .onTapGesture {
                        viewModel.currentPageIndex = index
                    }
            }
        }
        .padding(.bottom, 20)
    }
    
    private var gridColumns: [GridItem] {
        Array(repeating: GridItem(.flexible(), spacing: 10), count: settings.gridColumns)
    }
    
    private func makePage(_ apps: [AppItem]) -> some View {
        // Center the grid content in the page
        VStack {
            Spacer()
            LazyVGrid(columns: gridColumns, spacing: 20) {
                ForEach(apps) { app in
                    AppIconView(item: app, 
                               size: settings.iconSize, 
                               isSelected: viewModel.selectedAppID == app.bundleIdentifier)
                        .onTapGesture {
                            openApp(app)
                        }
                        .onHover { hovering in
                            if hovering { viewModel.selectedAppID = app.bundleIdentifier }
                        }
                }
            }
            .padding(40)
            Spacer()
        }
    }
    
    private func openApp(_ app: AppItem) {
        NSWorkspace.shared.open(URL(fileURLWithPath: app.path))
        // Close launcher behavior will go here
        NSApplication.shared.hide(nil)
    }
}

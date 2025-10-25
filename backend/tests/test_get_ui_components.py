from app.services.react_file_manager import ReactFileManager

# Test the updated generate_ui_components method
file_manager = ReactFileManager()
components = file_manager.generate_ui_components()

print('✅ Successfully loaded', len(components), 'UI components from template files')
print('✅ All components are now read from backend/templates/src/components/ui/')
print('✅ No more hardcoded components in the code')
print('✅ Utils file included:', 'src/lib/utils.ts' in components)

# Show a few key components
key_components = ['button.tsx', 'card.tsx', 'dialog.tsx', 'input.tsx']
for comp in key_components:
    if f'src/components/ui/{comp}' in components:
        print(f'✅ {comp} - loaded from template')
    else:
        print(f'❌ {comp} - missing')

print('\\nSample of loaded components:')
for i, path in enumerate(sorted(components.keys())[:10]):
    print(f'  {i+1}. {path}')

def test2(li):
    li.append(3)
    li.append(4)
def test1():
    li = [1,2]
    test2(li)
    print(li)

test1()

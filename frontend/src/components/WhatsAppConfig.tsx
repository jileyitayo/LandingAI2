'use client';

interface WhatsAppConfigProps {
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function WhatsAppConfig({ value, onChange, error }: WhatsAppConfigProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Allow only numbers, spaces, +, -, and ()
    const sanitized = e.target.value.replace(/[^0-9+\-\s()]/g, '');
    onChange(sanitized);
  };

  return (
    <div className="space-y-2">
      <label htmlFor="whatsapp" className="block text-sm font-medium text-gray-700">
        WhatsApp Business Number
      </label>
      <p className="text-xs text-gray-500 mb-2">
        Add your WhatsApp number to enable click-to-chat functionality on your site
      </p>
      <div className="mt-1">
        <input
          type="tel"
          id="whatsapp"
          value={value}
          onChange={handleChange}
          placeholder="+234 801 234 5678"
          className={`block w-full rounded-md shadow-sm px-3 py-2 border ${
            error
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500'
          } focus:outline-none focus:ring-2 sm:text-sm`}
          maxLength={20}
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      
      {/* Info box */}
      <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm">
        <div className="flex">
          <svg
            className="w-5 h-5 text-green-500 mr-2 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
          </svg>
          <div className="text-green-800">
            <p className="font-medium mb-1">WhatsApp Integration</p>
            <p className="text-xs">
              Visitors can contact you directly via WhatsApp. Include your country code
              (e.g., +234 for Nigeria, +254 for Kenya, +27 for South Africa).
            </p>
          </div>
        </div>
      </div>

      {value && (
        <div className="text-xs text-gray-500">
          <p>Preview: Visitors will see a chat button that opens WhatsApp with your number</p>
        </div>
      )}
    </div>
  );
}


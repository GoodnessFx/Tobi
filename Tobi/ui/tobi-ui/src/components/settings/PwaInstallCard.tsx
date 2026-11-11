"use client";

import { useEffect, useState } from "react";
import { onboardingApi } from "@/hooks/useTobiApi";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

interface DeviceContact {
  name?: string[];
  email?: string[];
  tel?: string[];
}

interface ContactPickerApi {
  getProperties: () => Promise<string[]>;
  select: (
    properties: string[],
    options?: { multiple?: boolean }
  ) => Promise<DeviceContact[]>;
}

export default function PwaInstallCard() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIos, setIsIos] = useState(false);
  const [showInstallHelp, setShowInstallHelp] = useState(false);
  const [installError, setInstallError] = useState("");
  const [contactPickerAvailable, setContactPickerAvailable] = useState(false);
  const [selectedContacts, setSelectedContacts] = useState<DeviceContact[]>([]);
  const [checkedContactIndexes, setCheckedContactIndexes] = useState<number[]>([]);
  const [contactBusy, setContactBusy] = useState(false);
  const [contactMessage, setContactMessage] = useState("");
  const [contactError, setContactError] = useState("");

  useEffect(() => {
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
    const platform = navigator.userAgent.toLowerCase();
    const ios =
      /iphone|ipad|ipod/.test(platform) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    setIsInstalled(standalone);
    setIsIos(ios);
    setContactPickerAvailable(
      Boolean((navigator as Navigator & { contacts?: ContactPickerApi }).contacts)
    );

    const handleInstallPrompt = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as BeforeInstallPromptEvent);
    };
    const handleInstalled = () => setIsInstalled(true);

    window.addEventListener("beforeinstallprompt", handleInstallPrompt);
    window.addEventListener("appinstalled", handleInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", handleInstallPrompt);
      window.removeEventListener("appinstalled", handleInstalled);
    };
  }, []);

  const install = async () => {
    setInstallError("");
    if (!installPrompt) {
      setShowInstallHelp((visible) => !visible);
      return;
    }
    try {
      await installPrompt.prompt();
      const choice = await installPrompt.userChoice;
      if (choice.outcome === "accepted") setIsInstalled(true);
      setInstallPrompt(null);
    } catch (error) {
      setInstallError(error instanceof Error ? error.message : "The install prompt failed.");
    }
  };

  const chooseContacts = async () => {
    setContactError("");
    setContactMessage("");
    try {
      const contactsApi = (navigator as Navigator & { contacts?: ContactPickerApi }).contacts;
      if (!contactsApi) {
        setContactPickerAvailable(false);
        return;
      }
      const supportedProperties = await contactsApi.getProperties();
      const properties = ["name", "email", "tel"].filter((property) =>
        supportedProperties.includes(property)
      );
      if (!properties.includes("name")) {
        setContactError("This browser cannot share contact names through its contact picker.");
        return;
      }
      const contacts = await contactsApi.select(properties, { multiple: true });
      setSelectedContacts(contacts);
      setCheckedContactIndexes(contacts.map((_, index) => index));
      setContactMessage(
        contacts.length ? "" : "No contacts were selected. Nothing was imported."
      );
    } catch (error) {
      setContactError(error instanceof Error ? error.message : "Could not open the contact picker.");
    }
  };

  const saveSelectedContacts = async () => {
    const contacts = checkedContactIndexes
      .map((index) => selectedContacts[index])
      .filter((contact): contact is DeviceContact => Boolean(contact));
    if (!contacts.length) {
      setContactError("Select at least one contact to import.");
      return;
    }
    setContactBusy(true);
    setContactError("");
    const failures: string[] = [];
    let imported = 0;
    try {
      for (const contact of contacts) {
        const name = contact.name?.find((value) => value.trim())?.trim();
        if (!name) {
          failures.push("A selected contact had no name.");
          continue;
        }
        try {
          await onboardingApi.createContact({
            name,
            email: contact.email?.[0] || "",
            phone: contact.tel?.[0] || "",
            source: "User-selected PWA contact import",
          });
          imported += 1;
        } catch (error) {
          failures.push(error instanceof Error ? `${name}: ${error.message}` : `${name}: import failed.`);
        }
      }
      if (imported) {
        setContactMessage(`Imported ${imported} contact${imported === 1 ? "" : "s"} to TOBI.`);
        setSelectedContacts([]);
        setCheckedContactIndexes([]);
      }
      if (failures.length) setContactError(failures.join(" "));
    } finally {
      setContactBusy(false);
    }
  };

  return (
    <section aria-labelledby="pwa-settings-title" className="space-y-5 rounded-xl border border-slate-200 p-4">
      <div>
        <h3 id="pwa-settings-title" className="text-sm font-semibold text-slate-900">Phone and app access</h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-600">
          Install TOBI on your home screen, or explicitly choose contacts to share. TOBI cannot read other apps in the background.
        </p>
        {isInstalled ? (
          <p className="mt-3 text-sm font-medium text-green-700">TOBI is installed on this device.</p>
        ) : (
          <>
            <button type="button" onClick={() => void install()} className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              {installPrompt ? "Install TOBI" : "How to install TOBI"}
            </button>
            {showInstallHelp && (
              <p className="mt-3 text-xs leading-relaxed text-slate-600">
                {isIos
                  ? "In Safari, tap Share, then Add to Home Screen."
                  : "Open your browser menu and choose Install app or Add to Home screen. If the option is missing, open TOBI from its deployed HTTPS address."}
              </p>
            )}
          </>
        )}
        {installError && <p role="alert" className="mt-2 text-xs text-red-700">{installError}</p>}
      </div>

      <div className="border-t border-slate-100 pt-4">
        <h4 className="text-sm font-medium text-slate-900">Import device contacts</h4>
        <p className="mt-1 text-xs leading-relaxed text-slate-600">
          Your browser may let you choose specific contacts. Nothing is sent until you review the selection and confirm the import.
        </p>
        {contactPickerAvailable ? (
          <button type="button" onClick={() => void chooseContacts()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50">
            Choose contacts
          </button>
        ) : (
          <p className="mt-3 text-xs text-slate-500">
            Contact selection is not supported by this browser. You can add contacts manually in TOBI CRM.
          </p>
        )}
        {selectedContacts.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs font-medium text-slate-700">Review selected contacts:</p>
            {selectedContacts.map((contact, index) => (
              <label key={`${contact.name?.[0] || "contact"}-${index}`} className="flex items-start gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={checkedContactIndexes.includes(index)}
                  onChange={(event) =>
                    setCheckedContactIndexes((current) =>
                      event.target.checked
                        ? [...current, index]
                        : current.filter((value) => value !== index)
                    )
                  }
                  className="mt-0.5 accent-blue-600"
                />
                <span>
                  {contact.name?.[0] || "Unnamed contact"}
                  {(contact.email?.[0] || contact.tel?.[0]) && (
                    <span className="block text-slate-500">
                      {[contact.email?.[0], contact.tel?.[0]].filter(Boolean).join(" · ")}
                    </span>
                  )}
                </span>
              </label>
            ))}
            <button type="button" disabled={contactBusy} onClick={() => void saveSelectedContacts()} className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {contactBusy ? "Importing…" : `Import ${checkedContactIndexes.length} selected`}
            </button>
          </div>
        )}
        {contactMessage && <p role="status" className="mt-2 text-xs text-green-700">{contactMessage}</p>}
        {contactError && <p role="alert" className="mt-2 text-xs text-red-700">{contactError}</p>}
      </div>
    </section>
  );
}

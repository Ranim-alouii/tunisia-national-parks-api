import React, { useState } from 'react';

const HealthOnboardingForm = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    // Allergies and sensitivities
    allergies: [],
    pollen_allergy: false,
    insect_sting_allergy: false,
    medication_allergy: '',

    // Physical conditions
    asthma: false,
    heart_condition: false,
    high_blood_pressure: false,
    diabetes: false,
    mobility_issues: false,

    // Physical capabilities
    physical_stamina: 'medium',
    walking_distance_limit: '',
    preferred_terrain: '',

    // Emergency contacts
    emergency_contact_name: '',
    emergency_contact_phone: '',
    medical_notes: '',

    // Medical information
    blood_type: '',
    current_medications: ''
  });

  const steps = [
    {
      title: "Bienvenue",
      subtitle: "Commençons par configurer votre profil de santé pour des recommandations personnalisées",
      content: "welcome"
    },
    {
      title: "Allergies et Sensibilités",
      subtitle: "Aidez-nous à identifier vos allergies et sensibilités",
      content: "allergies"
    },
    {
      title: "Conditions Médicales",
      subtitle: "Partagez vos conditions médicales pour votre sécurité",
      content: "conditions"
    },
    {
      title: "Capacités Physiques",
      subtitle: "Évaluez votre niveau d'activité physique",
      content: "physical"
    },
    {
      title: "Contacts d'Urgence",
      subtitle: "Ajoutez des contacts en cas d'urgence",
      content: "emergency"
    },
    {
      title: "Finalisation",
      subtitle: "Confirmez vos informations médicales",
      content: "summary"
    }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAllergyToggle = (allergy) => {
    setFormData(prev => ({
      ...prev,
      allergies: prev.allergies.includes(allergy)
        ? prev.allergies.filter(a => a !== allergy)
        : [...prev.allergies, allergy]
    }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Submit form
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      // Convert form data to match backend HealthProfileDB schema
      const healthProfile = {
        allergies: JSON.stringify(formData.allergies),
        pollen_allergy: formData.pollen_allergy,
        insect_sting_allergy: formData.insect_sting_allergy,
        medication_allergy: formData.medication_allergy,
        asthma: formData.asthma,
        heart_condition: formData.heart_condition,
        high_blood_pressure: formData.high_blood_pressure,
        diabetes: formData.diabetes,
        mobility_issues: formData.mobility_issues,
        physical_stamina: formData.physical_stamina,
        walking_distance_limit: formData.walking_distance_limit ? parseInt(formData.walking_distance_limit) : null,
        preferred_terrain: formData.preferred_terrain,
        emergency_contact_name: formData.emergency_contact_name,
        emergency_contact_phone: formData.emergency_contact_phone,
        medical_notes: formData.medical_notes,
        blood_type: formData.blood_type,
        current_medications: formData.current_medications
      };

      // Submit to backend
      const response = await fetch('/api/health/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(healthProfile)
      });

      if (response.ok) {
        onComplete(healthProfile);
      } else {
        console.error('Failed to save health profile');
      }
    } catch (error) {
      console.error('Error submitting health profile:', error);
    }
  };

  const renderStepContent = () => {
    switch (steps[currentStep].content) {
      case 'welcome':
        return (
          <div className="text-center py-8">
            <div className="mb-6">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Votre Profil de Santé</h2>
              <p className="text-gray-600 max-w-md mx-auto">
                Pour vous offrir des recommandations personnalisées et assurer votre sécurité,
                nous avons besoin de connaître vos informations médicales.
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-lg mx-auto">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div className="text-left">
                  <h4 className="text-sm font-medium text-blue-800">Confidentialité garantie</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Vos données médicales sont chiffrées et stockées en toute sécurité.
                    Elles ne seront utilisées que pour améliorer vos recommandations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'allergies':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Allergies connues</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {['Arachides', 'Fruits de mer', 'Lait', 'Œufs', 'Noix', 'Blé', 'Soja', 'Poisson'].map(allergy => (
                  <button
                    key={allergy}
                    onClick={() => handleAllergyToggle(allergy)}
                    className={`p-3 text-sm font-medium rounded-lg border transition-all ${
                      formData.allergies.includes(allergy)
                        ? 'bg-red-100 border-red-300 text-red-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:border-gray-400'
                    }`}
                  >
                    {allergy}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="pollen_allergy"
                  checked={formData.pollen_allergy}
                  onChange={(e) => handleInputChange('pollen_allergy', e.target.checked)}
                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                />
                <label htmlFor="pollen_allergy" className="ml-2 text-sm text-gray-700">
                  Allergie au pollen
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="insect_sting_allergy"
                  checked={formData.insect_sting_allergy}
                  onChange={(e) => handleInputChange('insect_sting_allergy', e.target.checked)}
                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                />
                <label htmlFor="insect_sting_allergy" className="ml-2 text-sm text-gray-700">
                  Allergie aux piqûres d'insectes
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Autres allergies médicamenteuses
              </label>
              <textarea
                value={formData.medication_allergy}
                onChange={(e) => handleInputChange('medication_allergy', e.target.value)}
                placeholder="Ex: pénicilline, aspirine..."
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                rows={3}
              />
            </div>
          </div>
        );

      case 'conditions':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Conditions médicales</h3>
              <p className="text-sm text-gray-600 mb-6">
                Cochez toutes les conditions médicales qui s'appliquent à vous.
                Ces informations nous aideront à adapter nos recommandations.
              </p>

              <div className="space-y-4">
                {[
                  { key: 'asthma', label: 'Asthme', icon: '🫁' },
                  { key: 'heart_condition', label: 'Problèmes cardiaques', icon: '❤️' },
                  { key: 'high_blood_pressure', label: 'Hypertension artérielle', icon: '🩸' },
                  { key: 'diabetes', label: 'Diabète', icon: '💉' },
                  { key: 'mobility_issues', label: 'Problèmes de mobilité', icon: '♿' }
                ].map(condition => (
                  <div key={condition.key} className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <span className="text-2xl mr-4">{condition.icon}</span>
                    <div className="flex-1">
                      <label htmlFor={condition.key} className="text-sm font-medium text-gray-900 cursor-pointer">
                        {condition.label}
                      </label>
                      <p className="text-xs text-gray-500 mt-1">
                        {condition.key === 'asthma' && 'Peut être aggravé par le pollen, la poussière ou l\'exercice intense'}
                        {condition.key === 'heart_condition' && 'L\'activité physique doit être adaptée selon les recommandations médicales'}
                        {condition.key === 'high_blood_pressure' && 'L\'altitude et la chaleur peuvent affecter la tension artérielle'}
                        {condition.key === 'diabetes' && 'La glycémie doit être surveillée pendant les randonnées'}
                        {condition.key === 'mobility_issues' && 'Les sentiers difficiles peuvent présenter des obstacles'}
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      id={condition.key}
                      checked={formData[condition.key]}
                      onChange={(e) => handleInputChange(condition.key, e.target.checked)}
                      className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes médicales supplémentaires (optionnel)
              </label>
              <textarea
                value={formData.medical_notes}
                onChange={(e) => handleInputChange('medical_notes', e.target.value)}
                placeholder="Informations médicales importantes, médicaments à prendre, etc."
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={4}
              />
            </div>
          </div>
        );

      case 'physical':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Évaluation physique</h3>
              <p className="text-sm text-gray-600 mb-6">
                Évaluez votre niveau d'endurance physique pour des recommandations adaptées.
              </p>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Niveau d'endurance physique
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'low', label: 'Faible', desc: 'Marche courte, escaliers difficiles' },
                    { value: 'medium', label: 'Moyen', desc: 'Marche modérée, bonne endurance' },
                    { value: 'high', label: 'Élevé', desc: 'Randonnée longue, très endurant' }
                  ].map(level => (
                    <button
                      key={level.value}
                      onClick={() => handleInputChange('physical_stamina', level.value)}
                      className={`p-4 border rounded-lg text-center transition-all ${
                        formData.physical_stamina === level.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <div className="font-medium">{level.label}</div>
                      <div className="text-xs text-gray-500 mt-1">{level.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Distance de marche maximale (mètres)
              </label>
              <input
                type="number"
                value={formData.walking_distance_limit}
                onChange={(e) => handleInputChange('walking_distance_limit', e.target.value)}
                placeholder="Ex: 2000"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Distance maximale que vous pouvez marcher confortablement
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Terrain préféré
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'flat', label: 'Plat', icon: '🏖️' },
                  { value: 'hilly', label: 'Collines', icon: '🏔️' },
                  { value: 'mountainous', label: 'Montagne', icon: '⛰️' }
                ].map(terrain => (
                  <button
                    key={terrain.value}
                    onClick={() => handleInputChange('preferred_terrain', terrain.value)}
                    className={`p-4 border rounded-lg text-center transition-all ${
                      formData.preferred_terrain === terrain.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="text-2xl mb-2">{terrain.icon}</div>
                    <div className="font-medium">{terrain.label}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 'emergency':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Contacts d'urgence</h3>
              <p className="text-sm text-gray-600 mb-6">
                En cas d'urgence, ces informations nous permettront de contacter rapidement quelqu'un.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom du contact d'urgence
                  </label>
                  <input
                    type="text"
                    value={formData.emergency_contact_name}
                    onChange={(e) => handleInputChange('emergency_contact_name', e.target.value)}
                    placeholder="Ex: Marie Dupont"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Numéro de téléphone d'urgence
                  </label>
                  <input
                    type="tel"
                    value={formData.emergency_contact_phone}
                    onChange={(e) => handleInputChange('emergency_contact_phone', e.target.value)}
                    placeholder="Ex: +216 XX XXX XXX"
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Informations médicales supplémentaires</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Groupe sanguin (optionnel)
                  </label>
                  <select
                    value={formData.blood_type}
                    onChange={(e) => handleInputChange('blood_type', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Non spécifié</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Médicaments actuels (optionnel)
                  </label>
                  <textarea
                    value={formData.current_medications}
                    onChange={(e) => handleInputChange('current_medications', e.target.value)}
                    placeholder="Listez vos médicaments actuels..."
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    rows={3}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'summary':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Profil terminé</h3>
              <p className="text-gray-600">
                Votre profil de santé a été configuré avec succès. Vous recevrez désormais des recommandations personnalisées.
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="font-medium text-gray-900 mb-4">Résumé de votre profil</h4>

              <div className="space-y-3 text-sm">
                {formData.allergies.length > 0 && (
                  <div>
                    <span className="font-medium">Allergies:</span> {formData.allergies.join(', ')}
                  </div>
                )}

                {formData.asthma && (
                  <div>
                    <span className="font-medium">Asthme:</span> Recommandations adaptées
                  </div>
                )}

                {formData.heart_condition && (
                  <div>
                    <span className="font-medium">Problèmes cardiaques:</span> Activité modérée recommandée
                  </div>
                )}

                {formData.high_blood_pressure && (
                  <div>
                    <span className="font-medium">Hypertension:</span> Surveillance de l'altitude
                  </div>
                )}

                {formData.physical_stamina && (
                  <div>
                    <span className="font-medium">Niveau physique:</span> {formData.physical_stamina}
                  </div>
                )}

                {formData.walking_distance_limit && (
                  <div>
                    <span className="font-medium">Distance de marche:</span> {formData.walking_distance_limit}m
                  </div>
                )}

                {formData.emergency_contact_name && (
                  <div>
                    <span className="font-medium">Contact d'urgence:</span> {formData.emergency_contact_name}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex">
                <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-blue-800">Recommandations personnalisées</h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Basé sur votre profil, nous vous recommanderons les parcs les plus adaptés
                    à votre condition physique et aux conditions météorologiques.
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const progressPercentage = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Progress Bar */}
      <div className="bg-white shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-gray-700">
              Étape {currentStep + 1} sur {steps.length}
            </span>
            <button
              onClick={onSkip}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Passer
            </button>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-lg shadow-lg">
          <div className="p-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900">{steps[currentStep].title}</h2>
              <p className="text-gray-600 mt-2">{steps[currentStep].subtitle}</p>
            </div>

            <div className="min-h-[400px]">
              {renderStepContent()}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={handleBack}
                disabled={currentStep === 0}
                className={`px-6 py-2 text-sm font-medium rounded-md transition-colors ${
                  currentStep === 0
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                Précédent
              </button>

              <button
                onClick={handleNext}
                className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
              >
                {currentStep === steps.length - 1 ? 'Terminer' : 'Suivant'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthOnboardingForm;

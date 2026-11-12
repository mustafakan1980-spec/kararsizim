from django import forms


class PollCreateForm(forms.Form):
    question = forms.CharField(
        label='Soru',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Neye karar veremiyorsun?',
            'class': 'form-input',
            'maxlength': '150',
            'id': 'id_question',
        })
    )

    def clean_question(self):
        question = self.cleaned_data.get('question', '').strip()
        if not question:
            raise forms.ValidationError('Soru alanı boş olamaz.')
        return question

    def clean(self):
        cleaned_data = super().clean()
        # Seçenekleri form datasından topla (option_0, option_1, ...)
        option_keys = sorted(
            [k for k in self.data.keys() if k.startswith('option_') and k.split('_')[1].isdigit()],
            key=lambda x: int(x.split('_')[1])
        )
        options = []
        for key in option_keys:
            val = self.data.get(key, '').strip()
            if val:
                options.append(val)

        if len(options) < 2:
            raise forms.ValidationError('En az 2 seçenek girmelisiniz.')
        if len(options) > 5:
            raise forms.ValidationError('En fazla 5 seçenek girebilirsiniz.')

        # Büyük/küçük harf duyarsız tekrar kontrolü
        seen = set()
        for opt in options:
            lowered = opt.lower()
            if lowered in seen:
                raise forms.ValidationError('Seçenekler birbirinin aynısı olamaz.')
            seen.add(lowered)

        cleaned_data['options'] = options
        return cleaned_data

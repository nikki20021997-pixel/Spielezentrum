import random
import time
import customtkinter as ctk

VALID_USERNAME = 'user'
VALID_PASSWORD = 'pass123'

DIFFICULTY_SETTINGS = {
    'leicht': {'label': 'Leicht', 'mult': 1, 'range': 10, 'pairs': 4, 'reaction_target': 1.7},
    'mittel': {'label': 'Mittel', 'mult': 1.5, 'range': 20, 'pairs': 6, 'reaction_target': 1.2},
    'schwer': {'label': 'Schwer', 'mult': 2, 'range': 50, 'pairs': 8, 'reaction_target': 0.9},
}

QUIZ_QUESTIONS = {
    'leicht': [
        {'question': 'Welches Tier bellt?', 'options': ['Katze', 'Hund', 'Vogel', 'Pferd'], 'answer': 'Hund'},
        {'question': 'Wie viele Tage hat eine Woche?', 'options': ['5', '6', '7', '8'], 'answer': '7'},
        {'question': 'Welche Farbe entsteht aus Blau und Gelb?', 'options': ['Grün', 'Rot', 'Lila', 'Orange'], 'answer': 'Grün'},
    ],
    'mittel': [
        {'question': 'Welcher Planet ist der dritte von der Sonne?', 'options': ['Mars', 'Erde', 'Venus', 'Jupiter'], 'answer': 'Erde'},
        {'question': 'Was ist 7 x 6?', 'options': ['42', '36', '48', '40'], 'answer': '42'},
        {'question': 'Welches Element hat das Symbol O?', 'options': ['Gold', 'Silber', 'Sauerstoff', 'Wasserstoff'], 'answer': 'Sauerstoff'},
    ],
    'schwer': [
        {'question': 'Wie heißt die Hauptstadt von Kanada?', 'options': ['Toronto', 'Vancouver', 'Ottawa', 'Montreal'], 'answer': 'Ottawa'},
        {'question': 'Wer schrieb "Faust"?', 'options': ['Schiller', 'Goethe', 'Kafka', 'Heine'], 'answer': 'Goethe'},
        {'question': 'Welche Zahl ist die Primzahl?', 'options': ['15', '21', '29', '33'], 'answer': '29'},
    ],
}

REWARD_LABELS = [
    (100, 'Goldmedaille'),
    (60, 'Silbermedaille'),
    (30, 'Bronzemedaille'),
]

class GameApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Login & Spielzentrum')
        self.geometry('840x700')
        self.resizable(True, True)
        self.configure(fg_color='#111827')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.stats = {
            'points': 0,
            'coins': 0,
            'levels': {
                'Zahlenraten': 1,
                'Quiz': 1,
                'Memory': 1,
                'Reaktion': 1,
            },
            'badges': [],
        }
        self.current_game = None
        self.difficulty = 'mittel'

        self.main_frame = ctk.CTkFrame(self, fg_color='#111827')
        self.main_frame.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self._show_login_screen()

    def _clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _show_login_screen(self):
        self._clear_frame()

        header = ctk.CTkLabel(
            self.main_frame,
            text='Willkommen zum Spielzentrum',
            font=ctk.CTkFont(size=30, weight='bold'),
            text_color='#e5e7eb',
        )
        header.grid(row=0, column=0, padx=24, pady=(24, 12), sticky='w')

        info = ctk.CTkLabel(
            self.main_frame,
            text='Melde dich an, um eines von vier Spielen mit Schwierigkeitsstufen, Level und Belohnungen zu spielen.',
            font=ctk.CTkFont(size=14),
            text_color='#cbd5e1',
            wraplength=760,
            justify='left',
        )
        info.grid(row=1, column=0, padx=24, pady=(0, 24), sticky='w')

        form_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        form_frame.grid(row=2, column=0, padx=24, pady=(0, 24), sticky='nsew')
        form_frame.grid_columnconfigure(0, weight=1)

        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text='Benutzername',
            width=420,
            height=45,
            fg_color='#111827',
            text_color='#e5e7eb',
            placeholder_text_color='#94a3b8',
        )
        self.username_entry.grid(row=0, column=0, padx=24, pady=(24, 12), sticky='ew')

        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text='Passwort',
            width=420,
            height=45,
            fg_color='#111827',
            text_color='#e5e7eb',
            placeholder_text_color='#94a3b8',
            show='*',
        )
        self.password_entry.grid(row=1, column=0, padx=24, pady=(0, 12), sticky='ew')

        self.show_password_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form_frame,
            text='Passwort anzeigen',
            variable=self.show_password_var,
            command=self._toggle_password_visibility,
            text_color='#cbd5e1',
            fg_color='#111827',
            hover=False,
        ).grid(row=2, column=0, padx=24, pady=(0, 18), sticky='w')

        self.login_message = ctk.CTkLabel(
            form_frame,
            text='',
            text_color='#f8fafc',
            font=ctk.CTkFont(size=12),
        )
        self.login_message.grid(row=3, column=0, padx=24, pady=(0, 8), sticky='w')

        ctk.CTkButton(
            form_frame,
            text='Anmelden',
            width=420,
            height=45,
            command=self._handle_login,
            fg_color='#38bdf8',
            hover_color='#0ea5e9',
            text_color='#111827',
            corner_radius=14,
        ).grid(row=4, column=0, padx=24, pady=(0, 24), sticky='ew')


    def _handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            self._show_game_center()
            return

        self.login_message.configure(text='Ungültige Anmeldedaten. Bitte erneut versuchen.', text_color='#f87171')

    def _toggle_password_visibility(self):
        self.password_entry.configure(show='' if self.show_password_var.get() else '*')

    def _show_status_summary(self):
        stats_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        stats_frame.grid(row=0, column=0, padx=24, pady=(0, 24), sticky='nsew')
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            stats_frame,
            text=f'Punkte\n{self.stats["points"]}',
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color='#38bdf8',
            justify='center',
        ).grid(row=0, column=0, padx=18, pady=24, sticky='ew')

        ctk.CTkLabel(
            stats_frame,
            text=f'Münzen\n{self.stats["coins"]}',
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color='#facc15',
            justify='center',
        ).grid(row=0, column=1, padx=18, pady=24, sticky='ew')

        level_text = '\n'.join([f'{game}: {level}' for game, level in self.stats['levels'].items()])
        ctk.CTkLabel(
            stats_frame,
            text=f'Level\n{level_text}',
            font=ctk.CTkFont(size=14),
            text_color='#e5e7eb',
            justify='center',
        ).grid(row=0, column=2, padx=18, pady=24, sticky='ew')

    def _show_game_center(self):
        self._clear_frame()
        self.current_game = None

        ctk.CTkLabel(
            self.main_frame,
            text='Spielauswahl',
            font=ctk.CTkFont(size=30, weight='bold'),
            text_color='#e5e7eb',
        ).grid(row=0, column=0, padx=24, pady=(24, 12), sticky='w')

        ctk.CTkLabel(
            self.main_frame,
            text='Wähle ein Spiel, lege die Schwierigkeit fest und sammle Punkte, Level und Belohnungen.',
            font=ctk.CTkFont(size=14),
            text_color='#cbd5e1',
            wraplength=760,
            justify='left',
        ).grid(row=1, column=0, padx=24, pady=(0, 24), sticky='w')

        self._show_status_summary()

        difficulty_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        difficulty_frame.grid(row=2, column=0, padx=24, pady=(0, 24), sticky='nsew')
        difficulty_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.difficulty_var = ctk.StringVar(value=self.difficulty)
        for index, key in enumerate(['leicht', 'mittel', 'schwer']):
            ctk.CTkRadioButton(
                difficulty_frame,
                text=DIFFICULTY_SETTINGS[key]['label'],
                variable=self.difficulty_var,
                value=key,
                text_color='#e5e7eb',
                hover_color='#0f172a',
                command=self._update_difficulty,
            ).grid(row=0, column=index, padx=24, pady=24, sticky='w')

        games_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        games_frame.grid(row=3, column=0, padx=24, pady=(0, 24), sticky='nsew')
        games_frame.grid_columnconfigure((0, 1), weight=1)

        game_buttons = [
            ('Zahlenraten', self._show_number_game),
            ('Quiz', self._show_quiz_game),
            ('Memory', self._show_memory_game),
            ('Reaktion', self._show_reaction_game),
        ]

        for index, (label, command) in enumerate(game_buttons):
            ctk.CTkButton(
                games_frame,
                text=label,
                command=command,
                width=320,
                height=70,
                fg_color='#38bdf8',
                hover_color='#0ea5e9',
                text_color='#111827',
                corner_radius=16,
                font=ctk.CTkFont(size=18, weight='bold'),
            ).grid(row=index // 2, column=index % 2, padx=24, pady=18, sticky='ew')

        ctk.CTkButton(
            self.main_frame,
            text='Abmelden',
            width=240,
            height=45,
            command=self._show_login_screen,
            fg_color='#f97316',
            hover_color='#fb923c',
            text_color='#ffffff',
            corner_radius=14,
        ).grid(row=4, column=0, padx=24, pady=(0, 24), sticky='w')

    def _update_difficulty(self):
        self.difficulty = self.difficulty_var.get()

    def _show_game_header(self, title, description):
        self._clear_frame()

        ctk.CTkLabel(
            self.main_frame,
            text=title,
            font=ctk.CTkFont(size=30, weight='bold'),
            text_color='#e5e7eb',
        ).grid(row=0, column=0, padx=24, pady=(24, 12), sticky='w')

        ctk.CTkLabel(
            self.main_frame,
            text=description,
            font=ctk.CTkFont(size=14),
            text_color='#cbd5e1',
            wraplength=760,
            justify='left',
        ).grid(row=1, column=0, padx=24, pady=(0, 24), sticky='w')

    def _show_footer_buttons(self):
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        footer_frame.grid(row=10, column=0, padx=24, pady=(12, 24), sticky='ew')
        footer_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer_frame,
            text='Zur Spielauswahl',
            command=self._show_game_center,
            fg_color='#3b82f6',
            hover_color='#60a5fa',
            text_color='#ffffff',
            corner_radius=14,
        ).grid(row=0, column=0, padx=(24, 12), pady=18, sticky='ew')

        ctk.CTkButton(
            footer_frame,
            text='Abmelden',
            command=self._show_login_screen,
            fg_color='#f97316',
            hover_color='#fb923c',
            text_color='#ffffff',
            corner_radius=14,
        ).grid(row=0, column=1, padx=(12, 24), pady=18, sticky='ew')

    def _add_points(self, base_points):
        earned = int(base_points * DIFFICULTY_SETTINGS[self.difficulty]['mult'])
        self.stats['points'] += earned
        self.stats['coins'] += max(1, earned // 5)
        return earned

    def _add_reward(self, earned):
        reward = 'Belohnung: '
        for threshold, label in REWARD_LABELS:
            if earned >= threshold:
                reward += label
                break
        else:
            reward += 'Teilnehmer-Abzeichen'
        self.stats['badges'].append(reward)
        return reward

    def _show_number_game(self):
        self.current_game = 'Zahlenraten'
        self.target_number = random.randint(1, DIFFICULTY_SETTINGS[self.difficulty]['range'])
        self.attempts = 0

        self._show_game_header(
            'Zahlenraten',
            f'Errate die Zahl zwischen 1 und {DIFFICULTY_SETTINGS[self.difficulty]["range"]} in so wenigen Versuchen wie möglich.',
        )

        self.game_input = ctk.CTkEntry(
            self.main_frame,
            placeholder_text='Gib deine Zahl ein',
            width=300,
            height=45,
            fg_color='#111827',
            text_color='#e5e7eb',
            placeholder_text_color='#94a3b8',
        )
        self.game_input.grid(row=2, column=0, padx=24, pady=(0, 12), sticky='w')

        ctk.CTkButton(
            self.main_frame,
            text='Raten',
            width=240,
            height=45,
            command=self._handle_number_guess,
            fg_color='#38bdf8',
            hover_color='#0ea5e9',
            text_color='#111827',
            corner_radius=14,
        ).grid(row=3, column=0, padx=24, pady=(0, 18), sticky='w')

        self.game_result_label = ctk.CTkLabel(
            self.main_frame,
            text='Viel Erfolg! Versuche: 0',
            font=ctk.CTkFont(size=14),
            text_color='#f8fafc',
            wraplength=760,
            justify='left',
        )
        self.game_result_label.grid(row=4, column=0, padx=24, pady=(0, 24), sticky='w')

        self._show_footer_buttons()

    def _handle_number_guess(self):
        guess = self.game_input.get().strip()
        if not guess.isdigit():
            self.game_result_label.configure(text='Bitte gib eine gültige Zahl ein.', text_color='#f87171')
            return

        guess = int(guess)
        self.attempts += 1

        if guess == self.target_number:
            earned = self._add_points(25 - self.attempts * 2)
            self.stats['levels'][self.current_game] += 1
            reward = self._add_reward(earned)
            self.game_result_label.configure(
                text=f'Richtig! Du hast die Zahl in {self.attempts} Versuchen erraten.\nDu erhältst {earned} Punkte, {reward}',
                text_color='#34d399',
            )
        elif guess < self.target_number:
            self.game_result_label.configure(text=f'Zu niedrig. Versuch {self.attempts}.', text_color='#fbbf24')
        else:
            self.game_result_label.configure(text=f'Zu hoch. Versuch {self.attempts}.', text_color='#fbbf24')

    def _show_quiz_game(self):
        self.current_game = 'Quiz'
        self.quiz_questions = QUIZ_QUESTIONS[self.difficulty].copy()
        self.quiz_index = 0
        self.correct_answers = 0

        self._show_game_header(
            'Quiz',
            'Beantworte die Fragen richtig. Pro richtiger Antwort gibt es Punkte und Level-Fortschritt.',
        )

        self.quiz_question_label = ctk.CTkLabel(
            self.main_frame,
            text='',
            font=ctk.CTkFont(size=16),
            text_color='#f8fafc',
            wraplength=760,
            justify='left',
        )
        self.quiz_question_label.grid(row=2, column=0, padx=24, pady=(0, 18), sticky='w')

        self.quiz_answer_var = ctk.StringVar(value='')
        self.quiz_buttons = []
        for index in range(4):
            btn = ctk.CTkButton(
                self.main_frame,
                text='',
                width=760,
                height=45,
                fg_color='#1f2937',
                hover_color='#0f172a',
                text_color='#e5e7eb',
                corner_radius=14,
                command=lambda idx=index: self._submit_quiz_answer(idx),
            )
            btn.grid(row=3 + index, column=0, padx=24, pady=(0, 12), sticky='ew')
            self.quiz_buttons.append(btn)

        self.quiz_result_label = ctk.CTkLabel(
            self.main_frame,
            text='Wähle eine Antwort aus.',
            font=ctk.CTkFont(size=14),
            text_color='#f8fafc',
            wraplength=760,
            justify='left',
        )
        self.quiz_result_label.grid(row=7, column=0, padx=24, pady=(0, 24), sticky='w')

        self._load_next_quiz_question()
        self._show_footer_buttons()

    def _load_next_quiz_question(self):
        if self.quiz_index >= len(self.quiz_questions):
            earned = self._add_points(30 + self.correct_answers * 10)
            self.stats['levels'][self.current_game] += 1
            reward = self._add_reward(earned)
            self.quiz_result_label.configure(
                text=f'Du hast {self.correct_answers}/{len(self.quiz_questions)} richtig beantwortet.\nDu bekommst {earned} Punkte, {reward}',
                text_color='#34d399',
            )
            for btn in self.quiz_buttons:
                btn.configure(state='disabled')
            return

        question = self.quiz_questions[self.quiz_index]
        self.quiz_question_label.configure(text=f'Frage {self.quiz_index + 1}: {question["question"]}')
        for index, option in enumerate(question['options']):
            self.quiz_buttons[index].configure(text=option, state='normal', fg_color='#1f2937')

    def _submit_quiz_answer(self, index):
        question = self.quiz_questions[self.quiz_index]
        answer = question['options'][index]
        if answer == question['answer']:
            self.correct_answers += 1
            self.quiz_result_label.configure(text='Richtig! Weiter zur nächsten Frage.', text_color='#34d399')
        else:
            self.quiz_result_label.configure(text=f'Falsch. Die richtige Antwort war {question["answer"]}.', text_color='#f87171')

        self.quiz_index += 1
        self.after(900, self._load_next_quiz_question)

    def _show_memory_game(self):
        self.current_game = 'Memory'
        pair_count = DIFFICULTY_SETTINGS[self.difficulty]['pairs']
        values = list(range(1, pair_count + 1)) * 2
        random.shuffle(values)
        self.memory_values = values
        self.memory_state = [False] * len(values)
        self.memory_buttons = []
        self.first_selection = None
        self.matches = 0

        self._show_game_header(
            'Memory',
            'Klicke Karten an und finde die passenden Paare. Je schneller du die Paare findest, desto besser.',
        )

        board_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        board_frame.grid(row=2, column=0, padx=24, pady=(0, 24), sticky='nsew')
        board_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        cols = 4
        for index in range(len(values)):
            button = ctk.CTkButton(
                board_frame,
                text='?',
                width=150,
                height=100,
                fg_color='#0f172a',
                hover_color='#1f2937',
                text_color='#e5e7eb',
                corner_radius=14,
                command=lambda idx=index: self._flip_memory_card(idx),
            )
            button.grid(row=index // cols, column=index % cols, padx=18, pady=18, sticky='nsew')
            self.memory_buttons.append(button)

        self.memory_result_label = ctk.CTkLabel(
            self.main_frame,
            text=f'Gefundene Paare: 0 / {pair_count}',
            font=ctk.CTkFont(size=14),
            text_color='#f8fafc',
        )
        self.memory_result_label.grid(row=3 + (len(values) // cols), column=0, padx=24, pady=(0, 18), sticky='w')

        self._show_footer_buttons()

    def _flip_memory_card(self, index):
        if self.memory_state[index] or self.first_selection == index:
            return

        self.memory_buttons[index].configure(text=str(self.memory_values[index]), fg_color='#38bdf8')
        if self.first_selection is None:
            self.first_selection = index
            return

        second_index = index
        first_index = self.first_selection
        if self.memory_values[first_index] == self.memory_values[second_index]:
            self.memory_state[first_index] = True
            self.memory_state[second_index] = True
            self.matches += 1
            self.memory_result_label.configure(text=f'Gefundene Paare: {self.matches} / {DIFFICULTY_SETTINGS[self.difficulty]["pairs"]}', text_color='#34d399')
            if self.matches == DIFFICULTY_SETTINGS[self.difficulty]['pairs']:
                earned = self._add_points(20 * self.difficulty_multiplier())
                self.stats['levels'][self.current_game] += 1
                reward = self._add_reward(earned)
                self.memory_result_label.configure(text=f'Du hast alle Paare gefunden! +{earned} Punkte, {reward}', text_color='#34d399')
        else:
            self.after(900, lambda: self._hide_memory_cards(first_index, second_index))

        self.first_selection = None

    def _hide_memory_cards(self, first_index, second_index):
        if not self.memory_state[first_index]:
            self.memory_buttons[first_index].configure(text='?', fg_color='#0f172a')
        if not self.memory_state[second_index]:
            self.memory_buttons[second_index].configure(text='?', fg_color='#0f172a')

    def difficulty_multiplier(self):
        return DIFFICULTY_SETTINGS[self.difficulty]['mult']

    def _show_reaction_game(self):
        self.current_game = 'Reaktion'
        self._show_game_header(
            'Reaktionsspiel',
            'Klicke den Knopf so schnell wie möglich, sobald er erscheint.',
        )

        self.reaction_button = ctk.CTkButton(
            self.main_frame,
            text='Starte Reaktion',
            width=240,
            height=60,
            fg_color='#38bdf8',
            hover_color='#0ea5e9',
            text_color='#111827',
            corner_radius=14,
            command=self._prepare_reaction_round,
        )
        self.reaction_button.grid(row=2, column=0, padx=24, pady=(0, 18), sticky='w')

        self.reaction_result_label = ctk.CTkLabel(
            self.main_frame,
            text='Drücke auf Start und warte auf den Knopf.',
            font=ctk.CTkFont(size=14),
            text_color='#f8fafc',
            wraplength=760,
            justify='left',
        )
        self.reaction_result_label.grid(row=3, column=0, padx=24, pady=(0, 24), sticky='w')

        self._show_footer_buttons()

    def _prepare_reaction_round(self):
        self.reaction_button.configure(state='disabled', text='Warte...')
        delay = random.randint(1000, 3000)
        self.after(delay, self._show_reaction_target)

    def _show_reaction_target(self):
        self.reaction_button.configure(state='normal', text='Klick mich!', fg_color='#f97316')
        self.start_time = time.perf_counter()
        self.reaction_button.configure(command=self._register_reaction)

    def _register_reaction(self):
        elapsed = time.perf_counter() - self.start_time
        base = max(1, 20 - int(elapsed * 10))
        earned = self._add_points(base * 2)
        self.stats['levels'][self.current_game] += 1
        reward = self._add_reward(earned)
        self.reaction_result_label.configure(
            text=f'Deine Reaktionszeit: {elapsed:.2f} s. Du erhältst {earned} Punkte, {reward}',
            text_color='#34d399',
        )
        self.reaction_button.configure(text='Starte Reaktion', fg_color='#38bdf8', command=self._prepare_reaction_round)

    def _show_footer_buttons(self):
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color='#1f2937', corner_radius=20, border_width=1, border_color='#334155')
        footer_frame.grid(row=20, column=0, padx=24, pady=(12, 24), sticky='ew')
        footer_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            footer_frame,
            text='Zur Spielauswahl',
            command=self._show_game_center,
            fg_color='#3b82f6',
            hover_color='#60a5fa',
            text_color='#ffffff',
            corner_radius=14,
        ).grid(row=0, column=0, padx=(24, 12), pady=18, sticky='ew')

        ctk.CTkButton(
            footer_frame,
            text='Abmelden',
            command=self._show_login_screen,
            fg_color='#f97316',
            hover_color='#fb923c',
            text_color='#ffffff',
            corner_radius=14,
        ).grid(row=0, column=1, padx=(12, 24), pady=18, sticky='ew')


if __name__ == '__main__':
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    app = GameApp()
    app.mainloop()

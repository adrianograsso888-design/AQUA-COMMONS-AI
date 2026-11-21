        r1.metric("Disponibilità", f"{availability:.1f} hm³")
        r2.metric("Domanda totale", f"{report_analysis['total_demand']:.1f} hm³")
        r3.metric("Acqua assegnata", f"{report_analysis['total_allocated']:.1f} hm³")
        r4.metric("Deficit complessivo", f"{report_analysis['total_shortage']:.1f} hm³")

        st.write(f"**Territorio:** {TERRITORY}")
        st.write(f"**Regione:** {REGION}")
        st.write(f"**Strategia approfondita:** {report_strategy_name}")
        st.write(f"**Copertura complessiva:** {report_analysis['coverage']:.1f}%")

        st.divider()
        st.subheader("2. Risultati dell'allocazione")
        st.dataframe(
            report_analysis["results_df"],
            hide_index=True,
            use_container_width=True,
        )
        st.bar_chart(
            report_analysis["results_df"].set_index("Settore")[
                ["Domanda (hm³)", "Acqua assegnata (hm³)"]
            ]
        )

        st.divider()
        st.subheader("3. Indicatori di impatto")
        impact1, impact2, impact3 = st.columns(3)

        with impact1:
            st.markdown("**Settori produttivi**")
            st.metric(
                "Deficit produttivo",
                f"{report_analysis['productive_shortage']:.2f} hm³",
            )
            st.caption("Volume non soddisfatto in agricoltura e industria; non è una perdita in euro.")

        with impact2:
            st.markdown("**Usi civili**")
            st.metric(
                "Copertura civile",
                f"{report_analysis['civil_coverage']:.1f}%",
            )
            st.caption(
                f"Deficit: {report_analysis['civil_shortage']:.2f} hm³"
            )

        with impact3:
            st.markdown("**Parametro ambientale**")
            st.metric(
                "Quota minima ipotizzata",
                f"{report_analysis['environmental_minimum']:.2f} hm³",
            )
            st.caption(
                f"Assegnata: {report_analysis['environmental_allocated']:.2f} hm³"
            )

        st.warning(
            "La quota ambientale è un parametro di scenario imposto dal modello. "
            "Il suo rispetto non costituisce una verifica del deflusso ecologico "
            "o della conformità normativa."
        )

        st.divider()
        st.subheader("4. Confronto tra strategie")
        st.dataframe(
            comparison_df,
            hide_index=True,
            use_container_width=True,
        )

        st.divider()
        st.subheader("5. Considerazioni per la valutazione")
        st.write(
            f"La strategia approfondita è **{report_strategy_name.lower()}**. "
            f"Il deficit complessivo risultante è "
            f"**{report_analysis['total_shortage']:.2f} hm³**."
        )

        if report_analysis["civil_shortage"] > 1e-6:
            st.warning(
                "La domanda civile inserita non è interamente soddisfatta. "
                "È necessario approfondire la tutela dei fabbisogni essenziali."
            )
        else:
            st.info(
                "La domanda civile inserita risulta interamente soddisfatta "
                "nei limiti delle ipotesi del modello."
            )

        if report_strategy == "priorità":
            st.write("**Ordine di priorità applicato:** " + " > ".join(priority))
        else:
            st.write(
                "**Ordine di priorità:** non applicabile alla strategia "
                "proporzionale."
            )

        st.caption(
            "Le considerazioni sono indicatori di supporto, non raccomandazioni "
            "automatiche. La valutazione finale compete alle autorità responsabili."
        )

        st.divider()
        st.subheader("6. Esportazione del documento")
        st.write(
            "Il PDF contiene sintesi, parametri, risultati settoriali, "
            "indicatori, confronto tra strategie e limiti del prototipo."
        )

        pdf_bytes = generate_pdf_report(
            report_analysis,
            availability,
            demands,
            minimums,
            report_strategy_name,
            priority,
            comparison_df,
        )

        st.download_button(
            label="📄 Scarica Decision Report in PDF",
            data=pdf_bytes,
            file_name="AQUA_COMMONS_AI_Decision_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

        st.caption(
            "Il documento è generato dai dati dello scenario corrente. "
